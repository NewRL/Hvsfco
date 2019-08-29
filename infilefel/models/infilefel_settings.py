# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import xml.etree.cElementTree as ElementTree
from datetime import datetime, timedelta
import pytz
import uuid
import xmltodict
import os
import json
from tempfile import gettempdir
import html
import base64

class infilefel_settings(models.Model):
    _name = "infilefel.settings"
    _description = "InFile FEL settings"

    ws_url_document = fields.Char('Document web service URL', default = 'https://')
    ws_url_void = fields.Char('Void document web service URL', default = 'https://')
    ws_url_signer = fields.Char('Signer web service URL', default = 'https://')
    ws_timeout = fields.Integer('Web service timeout', default=300)
    user = fields.Char('Certification user')
    sign_user = fields.Char('Sign user')
    sign_key = fields.Char('Sign key')
    certification_key = fields.Char('Certification key')
    infile_vat = fields.Char('InFile VAT')
    certificate_file = fields.Char('Certificate file')
    certificate_password = fields.Char('Certificate password')
    signing_type = fields.Selection([
        ('LOCAL', 'Sign documents using local program'),
        ('WS', 'Sign documents using Web Service'),
    ], string='Signing type', default='LOCAL')
    signer_location = fields.Char('Signer program location')
    organization_code = fields.Char('Organization code', default='1')
    vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default='GEN')
    isr_scenery = fields.Char('ISR sceneries')
    isr_phrases = fields.Char('ISR phrases')
    excempt_scenery = fields.Char('Excempt scenery')

    @api.multi
    def get_token(self):
        if self.ws_url_token:
            if self.user:
                if self.api_key:
                    headers = {
                        'Content-Type': 'application/xml',
                    }
                    data = "<SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>".format(self.user, self.api_key)
                    try:
                        response = requests.post(self.ws_url_token, headers=headers, data=data)
                        if response.ok:
                            text = ElementTree.fromstring(response.text)
                            token_tag = text.findall('token')
                            if token_tag:
                                self.token = token_tag[0].text
                            due_date_tag = text.findall('vigencia')
                            if due_date_tag:
                                token_due_date = datetime.strptime(due_date_tag[0].text[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone(self.env.user.tz))
                                self.token_due_date = token_due_date
                    except Exception as e:
                        raise UserError(_('infilefel: Error consuming web service: {}').format(e.message))
                else:
                    raise UserError( _('infilefel: API key not set'))
            else:
                raise UserError(_('infilefel: User not set'))
        else:
            raise UserError(_('infilefel: Web service URL for tokens not set'))

    @api.multi
    def sign_document(self, invoice):

        def escape_string(value):
            # return value.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt').replace('"', '&quot;').replace("'", '&apos;')
            return html.escape(value).encode("ascii", "xmlcharrefreplace").decode('utf8')

        token = None
        if not invoice.journal_id.infilefel_type:
            return
        elif invoice.journal_id.infilefel_type == '':
            return
        elif invoice.infilefel_sat_uuid:
            raise UserError(_('Document is already signed'))
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        else:
            parter_vat = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'
            partner_name = escape_string(invoice.partner_id.name)
            # xml_vat = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><RetornaDatosClienteRequest><nit>{}</nit></RetornaDatosClienteRequest>'.format('81109032')
            # headers = {
            #     'Content-Type': 'application/xml',
            #     'Authorization': 'Bearer {}'.format(self.token)
            # }
            # try:
            #     response = requests.post('https://dev.api.ifacere-fel.com/fel-dte-services/api/retornarDatosCliente', headers=headers, data=xml_vat)
            #     if response.ok:
            #         result = xmltodict.parse(response.text)
            #         if result['RetornaDatosClienteResponse']['tipo_respuesta'] == '1':
            #             error_message = u''
            #             if type(result['RetornaDatosClienteResponse']['listado_errores']['error']) is list:
            #                 for message in result['RetornaDatosClienteResponse']['listado_errores']['error']:
            #                     error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
            #             else:
            #                 error_message += '\n{}: {}'.format(
            #                     result['RetornaDatosClienteResponse']['listado_errores']['error']['cod_error'],
            #                     result['RetornaDatosClienteResponse']['listado_errores']['error']['desc_error'])
            #             raise UserError(error_message)
            #         else:
            #             partner_name = result['RetornaDatosClienteResponse']['nombre']
            #     else:
            #         raise UserError(_('infilefel: Response error validating VAT: {}').format(str(response.text)))
            # except Exception as e:
            #     error_message = ''
            #     if hasattr(e, 'object'):
            #         if hasattr(e, 'reason'):
            #             error_message = u"{}: {}".format(e.reason, e.object)
            #         else:
            #             error_message = u" {}".format(e.object)
            #     elif hasattr(e, 'message'):
            #         error_message = e.message
            #     elif hasattr(e, 'name'):
            #         error_message = e.name
            #     else:
            #         error_message = e
            #     raise UserError(_('infilefel: Error consuming web service: {}').format(error_message))
            if not invoice.infilefel_uuid:
                invoice.infilefel_uuid = str(uuid.uuid4())

            #
            # Líneas del documento
            #
            excempt = False
            excempt_phrase = False
            xml_lines = ''
            taxes = []
            line_number = 0
            for line in invoice.invoice_line_ids:
                line_number += 1
                if line.invoice_line_tax_ids:
                    line_gross = round(line.price_unit * line.quantity, 2)
                    line_discount = round(line_gross * line.discount / 100, 2)
                    line_amount = line_gross - line_discount
                else:
                    line_gross = line.price_subtotal
                    line_discount = round(line_gross * line.discount / 100, 2)
                    line_amount = line_gross - line_discount


                xml_lines += """<dte:Item BienOServicio="{BienOServicio}" NumeroLinea="{NumeroLinea}">
                        <dte:Cantidad>{Cantidad}</dte:Cantidad>
                        <dte:UnidadMedida>{UnidadMedida}</dte:UnidadMedida>
                        <dte:Descripcion>{Descripcion}</dte:Descripcion>
                        <dte:PrecioUnitario>{PrecioUnitario}</dte:PrecioUnitario>
                        <dte:Precio>{Precio}</dte:Precio>
                        <dte:Descuento>{Descuento}</dte:Descuento>{TituloImpuestos}""".format(
                    BienOServicio='S' if line.product_id.type == 'service' else 'B',
                    NumeroLinea=line_number,
                    Cantidad=line.quantity,
                    UnidadMedida = escape_string(line.uom_id.name)[:3],
                    Descripcion=escape_string(line.name),
                    PrecioUnitario=line.price_unit,
                    Precio=line_gross,
                    Descuento=line_discount,
                    TituloImpuestos='' if invoice.journal_id.infilefel_type in ['NABN'] else '<dte:Impuestos>'
                )
                # UnidadMedida = escape_string(line.uom_id.name[:3]),

                line_taxes = 0
                if invoice.journal_id.infilefel_type not in ['NABN']:
                    for tax_id in line.invoice_line_tax_ids:
                        amount = 0
                        if invoice.journal_id.infilefel_type not in ['NABN'] and tax_id.amount_type == 'percent':
                            amount = round(line_amount * tax_id.amount / (100 + tax_id.amount), 2)
                        line_taxes += amount
                        xml_lines += """<dte:Impuesto>
                                <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                                <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                                <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                                <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>
                            </dte:Impuesto>
                        """.format(
                            NombreCorto=tax_id.infilefel_sat_code,
                            CodigoUnidadGravable='1',
                            MontoGravable=line.price_subtotal,
                            MontoImpuesto=amount
                        )
                        tax_added = False
                        for tax_sum in taxes:
                            if tax_sum['NombreCorto'] == tax_id.infilefel_sat_code:
                                tax_added = True
                                tax_sum['Valor'] += amount
                        if not tax_added:
                            taxes.append({
                                'NombreCorto': tax_id.infilefel_sat_code,
                                'Valor': amount
                            })
                if invoice.journal_id.infilefel_type not in ['NABN'] and line_taxes == 0:
                    excempt = True
                    xml_lines += """<dte:Impuesto>
                            <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                            <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                            <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                            <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>
                        </dte:Impuesto>
                    """.format(
                        NombreCorto='IVA',
                        CodigoUnidadGravable='2',
                        MontoGravable=line.price_subtotal,
                        MontoImpuesto=0
                    )
                    tax_added = False
                    for tax_sum in taxes:
                        if tax_sum['NombreCorto'] == 'IVA':
                            tax_added = True
                            tax_sum['Valor'] += 0
                    if not tax_added:
                        taxes.append({
                            'NombreCorto': 'IVA',
                            'Valor': 0
                        })

                xml_lines += """{TituloImpuestos}
                        <dte:Total>{Total}</dte:Total>
                    </dte:Item>
                """.format(TituloImpuestos='' if invoice.journal_id.infilefel_type in ['NABN'] else '</dte:Impuestos>', Total=line_amount)

            #
            # Frases
            #
            xml_phrases = ''
            if invoice.journal_id.infilefel_type not in ['NCRE', 'NDEB', 'NABN']:
                xml_phrases = '<dte:Frases>'
                for scenary in self.isr_scenery.split(','):
                    for phrase in self.isr_phrases.split(','):
                        xml_phrases += '<dte:Frase CodigoEscenario="{CodigoEscenario}" TipoFrase="{TipoFrase}" />'.format(
                            CodigoEscenario=scenary,
                            TipoFrase=phrase
                        )
                if excempt and not excempt_phrase:
                    xml_phrases += '<dte:Frase CodigoEscenario="{CodigoEscenario}" TipoFrase="{TipoFrase}" />'.format(
                        CodigoEscenario=self.excempt_scenery,
                        TipoFrase='4'
                    )
                    excempt_phrase = True
                xml_phrases += '</dte:Frases>'
            if xml_phrases == '<dte:Frases></dte:Frases>':
                xml_phrases = ''

            #
            # Encabezado del documento
            #
            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz))
            sign_date_utc = datetime.now().replace(tzinfo=pytz.UTC)
            current_date = sign_date.strftime('%Y-%m-%dT%H:%M:%S-06:00')
            current_time = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz)).strftime('%H:%M:%S-06:00')
            # invoice_sign_date = invoice.date_invoice + current_time
            invoice_sign_date = invoice.date_invoice.strftime('%Y-%m-%dT') + current_time
            xml = """<?xml version="1.0" encoding="UTF-8"?><dte:GTDocumento Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
            <dte:SAT ClaseDocumento="dte">
                <dte:DTE ID="DatosCertificados">
                    <dte:DatosEmision ID="DatosEmision">
                        <dte:DatosGenerales CodigoMoneda="{CodigoMoneda}" {EXP} FechaHoraEmision="{FechaHoraEmision}" {NumeroAcceso} Tipo="{Tipo}"/>
                        <dte:Emisor AfiliacionIVA="{AfiliacionIVA}" CodigoEstablecimiento="{CodigoEstablecimiento}" CorreoEmisor="{CorreoEmisor}" NITEmisor="{NITEmisor}" NombreComercial="{NombreComercial}" NombreEmisor="{NombreEmisor}">
                            <dte:DireccionEmisor>
                                <dte:Direccion>{DireccionEmisor}</dte:Direccion>
                                <dte:CodigoPostal>{CodigoPostalEmisor}</dte:CodigoPostal>
                                <dte:Municipio>{MunicipioEmisor}</dte:Municipio>
                                <dte:Departamento>{DepartamentoEmisor}</dte:Departamento>
                                <dte:Pais>{PaisEmisor}</dte:Pais>
                            </dte:DireccionEmisor>
                        </dte:Emisor>
                        <dte:Receptor CorreoReceptor="{CorreoReceptor}" IDReceptor="{NITReceptor}" NombreReceptor="{NombreReceptor}">
                            <dte:DireccionReceptor>
                                <dte:Direccion>{DireccionReceptor}</dte:Direccion>
                                <dte:CodigoPostal>{CodigoPostal}</dte:CodigoPostal>
                                <dte:Municipio>{Municipio}</dte:Municipio>
                                <dte:Departamento>{Departamento}</dte:Departamento>
                                <dte:Pais>{Pais}</dte:Pais>
                            </dte:DireccionReceptor>
                        </dte:Receptor>
                        {Frases}
                        <dte:Items>
                            {Items}
                        </dte:Items>
                        <dte:Totales>
                            {TituloImpuestos}""".format(
                    CodigoMoneda=invoice.currency_id.name,
                    EXP='',  # Para exportaciones: 'EXP="SI"'
                    FechaHoraEmision=invoice_sign_date,
                    NumeroAcceso='',
                    Tipo=invoice.journal_id.infilefel_type,
                    AfiliacionIVA=self.vat_affiliation,
                    CodigoEstablecimiento=self.organization_code,
                    CorreoEmisor=invoice.company_id.email if invoice.company_id.email else '',
                    NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    NombreComercial=escape_string(invoice.company_id.name),
                    NombreEmisor=escape_string(invoice.company_id.name),
                    DireccionEmisor=escape_string((invoice.company_id.street if invoice.company_id.street else '') + (' ' + invoice.company_id.street2 if invoice.company_id.street2 else '')),
                    CodigoPostalEmisor=invoice.company_id.zip if invoice.company_id.zip else '01001',
                    MunicipioEmisor=escape_string(invoice.company_id.city if invoice.company_id.city else ''),
                    DepartamentoEmisor=escape_string(invoice.company_id.state_id.name if invoice.company_id.state_id else ''),
                    PaisEmisor=escape_string(invoice.company_id.country_id.code if invoice.company_id.country_id else ''),
                    DireccionReceptor=escape_string((invoice.partner_id.street if invoice.partner_id.street else '') + (' ' + invoice.partner_id.street2 if invoice.partner_id.street2 else '')),
                    CorreoReceptor=invoice.partner_id.email if invoice.partner_id.email else '',
                    NITReceptor=invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF',
                    NombreReceptor=escape_string(invoice.partner_id.name),
                    CodigoPostal=invoice.partner_id.zip if invoice.partner_id.zip else '01001',
                    Municipio=escape_string(invoice.partner_id.city if invoice.partner_id.city else ''),
                    Departamento=escape_string(invoice.partner_id.state_id.name if invoice.partner_id.state_id else ''),
                    Pais=escape_string(invoice.partner_id.country_id.code if invoice.partner_id.country_id else ''),
                    Frases=xml_phrases,
                    Items=xml_lines,
                    TituloImpuestos='' if invoice.journal_id.infilefel_type in ['NABN'] else '<dte:TotalImpuestos>'
                )
            # xml += """</dte:Items>
            #                 <dte:Totales>
            #                 <dte:TotalImpuestos>
            # """
            if not invoice.journal_id.infilefel_type in ['NABN']:
                for tax in taxes:
                    xml += '<dte:TotalImpuesto NombreCorto="{NombreCorto}" TotalMontoImpuesto="{TotalMontoImpuesto}"/>'.format(
                        NombreCorto=tax['NombreCorto'],
                        TotalMontoImpuesto=tax['Valor']
                    )

            extras = ''
            if invoice.journal_id.infilefel_type == 'FCAM':
                extras = """
                            <dte:Complementos>
                                <dte:Complemento IDComplemento="AbonosFacturaCambiaria" NombreComplemento="AbonosFacturaCambiaria" URIComplemento="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0">
                                    <cfc:AbonosFacturaCambiaria xmlns:cfc="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0" Version="1">
                                        <cfc:Abono>
                                            <cfc:NumeroAbono>1</cfc:NumeroAbono>
                                            <cfc:FechaVencimiento>{FechaVencimiento}</cfc:FechaVencimiento>
                                            <cfc:MontoAbono>{Monto}</cfc:MontoAbono>
                                        </cfc:Abono>
                                    </cfc:AbonosFacturaCambiaria>
                                </dte:Complemento>
                            </dte:Complementos>""".format(FechaVencimiento=invoice.date_due, Monto=invoice.amount_total)
            elif invoice.journal_id.infilefel_type in ['NCRE', 'NDEB']:
                extras = """
                            <dte:Complementos>
                                <dte:Complemento IDComplemento="{IDComplemento}" NombreComplemento="{NombreComplemento}" URIComplemento="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0">
                                    {Referencias}
                                </dte:Complemento>
                            </dte:Complementos>"""
                references = """<cno:ReferenciasNota xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"
                                        Version="1" {RegimenAnterior}
                                        NumeroAutorizacionDocumentoOrigen="{DocumentoOrigen}"
                                        FechaEmisionDocumentoOrigen="{FechaEmision}" {MotivoAjuste}
                                    />
                """
                id_complemento = ''
                nombre_complemento = ''
                if invoice.refund_invoice_id:
                    previous_regime = ''
                    original_document = invoice.origin
                    reason = ''
                    if invoice.refund_invoice_id.infilefel_sat_uuid:
                        id_complemento = 'ReferenciasNota'
                        nombre_complemento = 'ReferenciasNota'
                        original_document = invoice.refund_invoice_id.infilefel_sat_uuid
                        reason = 'MotivoAjuste="{}"'.format(invoice.name)
                    else:
                        id_complemento = 'ComplementoReferenciaNota'
                        nombre_complemento = 'Complemento Referencia Nota'
                        previous_regime = 'RegimenAntiguo="Antiguo"'
#                            original_document = invoice.refund_invoice_id.journal_id.infilefel_previous_authorization
                        original_document = invoice.refund_invoice_id.resolution_id.name
#                            reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.journal_id.infilefel_previous_serial, invoice.refund_invoice_id.name)
                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.gface_dte_serial[8:9], str(int(invoice.refund_invoice_id.gface_dte_number[16:100])) )

                    references = references.format(
                        RegimenAnterior=previous_regime,
                        DocumentoOrigen=original_document,
                        FechaEmision=invoice.refund_invoice_id.date_invoice,
                        MotivoAjuste=reason,
                    )
                else:
                    id_complemento = 'ComplementoReferenciaNota'
                    nombre_complemento = 'Complemento Referencia Nota'
#                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.journal_id.infilefel_previous_serial, invoice.name)
                    reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.gface_dte_serial, invoice.refund_invoice_id.resolution_id.name)
                    references = references.format(
                        RegimenAnterior='RegimenAntiguo="Antiguo"',
                        DocumentoOrigen=invoice.journal_id.infilefel_previous_authorization,
                        FechaEmision=invoice.date_invoice,
                        MotivoAjuste=reason,
                    )
                extras = extras.format(
                    IDComplemento=id_complemento,
                    NombreComplemento=nombre_complemento,
                    Referencias=references
                )

            xml += """{TituloImpuestos}
                            <dte:GranTotal>{GranTotal}</dte:GranTotal>
                            </dte:Totales>{Complementos}
                        </dte:DatosEmision>
                    </dte:DTE>
                </dte:SAT>
</dte:GTDocumento>""".format(TituloImpuestos='' if invoice.journal_id.infilefel_type in ['NABN'] else '</dte:TotalImpuestos>', GranTotal=invoice.amount_total, Complementos=extras)
            source_xml = xml

            xmlb64 = ''
            sign_document = False
            if self.signing_type == 'LOCAL':
                tmp_dir = gettempdir()
                source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.infilefel_uuid))
                signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.infilefel_uuid))
                with open(source_xml_file, 'w', encoding="utf-8") as xml_file:
                    xml_file.write(xml)
                # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/Xadesinfilefel.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.infilefel_uuid))
                os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.infilefel_uuid, tmp_dir, 'DatosEmision'))

                if os.path.isfile(signed_xml_file):
                    with open(signed_xml_file, 'r') as myfile:
                        xml = myfile.read()
                    sign_document = True
                else:
                    raise UserError(_('infilefel: Signed XML file not found'))
            else:
                data = {
                    'llave': self.sign_key,
                    'archivo': base64.b64encode(xml.encode('utf-8')).decode('utf-8'),
                    'codigo': invoice.infilefel_uuid,
                    'alias': self.sign_user,
                    "es_anulacion": 'N'
                }
                sign_response = requests.post(url=self.ws_url_signer, json=data)
                result = json.loads(sign_response.text)
                if result['resultado']:
                    xmlb64 = result['archivo']
                    xml = base64.b64decode(xmlb64).decode('utf-8')
                    sign_document = True
                else:
                    raise UserError(_('Error signing document: {}').format(result['descripcion']))

            if sign_document:
                headers = {
                    'usuario': self.user,
                    'llave': self.certification_key,
                    'identificador': invoice.infilefel_uuid,
                    'Content-Type': 'application/json',
                }
                data = {
                    'nit_emisor': invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    'correo_copia': 'ORamirezO@gmail.com',
                    'xml_dte': xmlb64
                }
                try:
                    response = requests.post(self.ws_url_document, headers=headers, data=json.dumps(data))
                    if response.ok:
                        result = json.loads(response.text)
                        if result['resultado']:
                            invoice.write({
                                'infilefel_sign_date': invoice_sign_date,
                                'infilefel_sat_uuid': result['uuid'],
                                'infilefel_source_xml': source_xml,
                                'infilefel_signed_xml': xml,
                                'infilefel_result_xml': result['xml_certificado'],
                            })
                        else:
                            error_message = u''
                            if type(result['descripcion_errores']) is list:
                                for message in result['descripcion_errores']:
                                    error_message += '\n{}: {}'.format(message['fuente'], message['mensaje_error'])
                            else:
                                error_message += '\n{}: {}'.format(
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error']['cod_error'],
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                            raise UserError(error_message)
                    else:
                        raise UserError(_('infilefel: Response error consuming web service: {}').format(str(response.text)))
                except Exception as e:
                    error_message = ''
                    if hasattr(e, 'object'):
                        if hasattr(e, 'reason'):
                            error_message = u"{}: {}".format(e.reason, e.object)
                        else:
                            error_message = u" {}".format(e.object)
                    elif hasattr(e, 'message'):
                        error_message = e.message
                    elif hasattr(e, 'name'):
                        error_message = e.name
                    else:
                        error_message = e
                    raise UserError(_('infilefel: Error consuming web service: {}').format(error_message))
            else:
                raise UserError(_('infilefel Signer: {}').format(result['message']))

    @api.multi
    def void_document(self, invoice):
        token = None
        if not invoice.journal_id.infilefel_type:
            return
        elif invoice.journal_id.infilefel_type == '':
            return
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        elif self.token_due_date:
            if self.token_due_date >= fields.Datetime.now():
                if not invoice.infilefel_void_uuid:
                    invoice.infilefel_void_uuid = str(uuid.uuid4())

                current_date = datetime.now().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.env.user.tz))

                xml = """<?xml version="1.0" encoding="UTF-8"?><dte:GTAnulacionDocumento Version="0.1" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
                <dte:SAT>
                    <dte:AnulacionDTE ID="DatosCertificados">
                        <dte:DatosGenerales ID="DatosAnulacion"
                            NumeroDocumentoAAnular="{NumeroDocumentoAAnular}"
                            NITEmisor="{NITEmisor}"
                            IDReceptor="{IDReceptor}"
                            FechaEmisionDocumentoAnular="{FechaEmisionDocumentoAnular}"
                            FechaHoraAnulacion="{FechaHoraAnulacion}"
                            MotivoAnulacion="Cancelacion"
                        />
                        <dte:Certificacion>
                            <dte:NITCertificador>{NITCertificador}</dte:NITCertificador>
                            <dte:NombreCertificador>{NombreCertificador}</dte:NombreCertificador>
                            <dte:FechaHoraCertificacion>{FechaHoraCertificacion}</dte:FechaHoraCertificacion>
                        </dte:Certificacion>
                    </dte:AnulacionDTE>
                </dte:SAT></dte:GTAnulacionDocumento>""".format(
                        NumeroDocumentoAAnular=invoice.infilefel_sat_uuid,
                        NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                        IDReceptor=invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF',
                        FechaEmisionDocumentoAnular=invoice.date_invoice + 'T00:00:00-06:00',
                        FechaHoraAnulacion=current_date.replace(microsecond=1).isoformat().replace('.000001', '.000'),
                        NITCertificador=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                        NombreCertificador=invoice.company_id.name,
                        FechaHoraCertificacion=invoice.date_invoice + 'T00:00:00-06:00',
                    )

                source_xml = xml

                # tmp_dir = gettempdir()
                # source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.infilefel_void_uuid))
                # signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.infilefel_void_uuid))
                # with open(source_xml_file, 'w') as xml_file:
                #     xml_file.write(xml)
                # os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.infilefel_void_uuid, tmp_dir, 'DatosGenerales'))
                #
                # if not os.path.isfile(signed_xml_file):
                #     raise UserError(_('infilefel: Signed XML file not found'))
                # elif self.token:
                sign_document = False
                if self.signing_type == 'LOCAL':
                    tmp_dir = gettempdir()
                    source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.infilefel_void_uuid))
                    signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.infilefel_void_uuid))
                    with open(source_xml_file, 'w') as xml_file:
                        xml_file.write(xml)
                    # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/Xadesinfilefel.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.infilefel_uuid))
                    os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.infilefel_void_uuid, tmp_dir, 'DatosGenerales'))

                    if os.path.isfile(signed_xml_file):
                        with open(signed_xml_file, 'r') as myfile:
                            xml = myfile.read()
                        sign_document = True
                    else:
                        raise UserError(_('infilefel: Signed XML file not found'))
                else:
                    sign_response = requests.post(url=self.ws_url_signer, data={'XML': xml, 'UUID': invoice.infilefel_void_uuid, 'Main_Tag': 'DatosGenerales'})
                    result = json.loads(sign_response.text)
                    if result['success']:
                        xml = result['signed_xml'].encode('utf-8')
                        sign_document = True
                    else:
                        raise UserError(_('Error signing document: {}').format(result['message']))

                if sign_document:
                    headers = {
                        'Content-Type': 'application/xml',
                        'Authorization': 'Bearer {}'.format(self.token)
                    }
                    data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><AnulaDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></AnulaDocumentoXMLRequest>'.format(invoice.infilefel_void_uuid.upper(), xml)
                    try:
                        response = requests.post(self.ws_url_void, headers=headers, data=data)
                        if response.ok:
                            result = xmltodict.parse(response.text)
                            if result['AnulaDocumentoXMLResponse']['tipo_respuesta'] == '1':
                                error_message = ''
                                if type(result['AnulaDocumentoXMLResponse']['listado_errores']['error']) is list:
                                    for message in result['AnulaDocumentoXMLResponse']['listado_errores']['error']:
                                        error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
                                else:
                                    error_message += '\n{}: {}'.format(result['AnulaDocumentoXMLResponse']['listado_errores']['error']['cod_error'], result['AnulaDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                                raise UserError(error_message)
                            else:
                                invoice.write({
                                    'infilefel_void_sat_uuid': result['AnulaDocumentoXMLResponse']['uuid'],
                                    'infilefel_void_source_xml': source_xml,
                                    'infilefel_void_signed_xml': xml,
                                    'infilefel_void_result_xml': result['AnulaDocumentoXMLResponse']['xml_dte'],
                                })
                                invoice.action_invoice_cancel()
                        else:
                            raise UserError(_('infilefel: Response error consuming web service: {}').format(str(response.text)))
                    except Exception as e:
                        error_message = ''
                        if hasattr(e, 'object'):
                            if hasattr(e, 'reason'):
                                error_message = u"{}: {}".format(e.reason, e.object)
                            else:
                                error_message = u" {}".format(e.object)
                        elif hasattr(e, 'message'):
                            error_message = e.message
                        elif hasattr(e, 'name'):
                            error_message = e.name
                        else:
                            error_message = e
                        raise UserError(_('infilefel: Error consuming web service: {}').format(error_message))
                else:
                    raise UserError(_('infilefel: API key not set'))
            else:
                raise UserError(_('infilefel: Token expired'))
        else:
            raise UserError(_('infilefel: Token not set'))

class infilefel_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = "infilefel.config.settings"
    _description = "InFile FEL settings configurator"

    @api.model
    def _default_ws_url_token(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].ws_url_token
        return value

    @api.model
    def _default_ws_url_document(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].ws_url_document
        return value

    @api.model
    def _default_ws_url_void(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].ws_url_void
        return value

    @api.model
    def _default_ws_url_signer(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].ws_url_signer
        return value

    @api.model
    def _default_ws_timeout(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].ws_timeout
        return value

    @api.model
    def _default_user(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].user
        return value

    @api.model
    def _default_sign_user(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].sign_user
        return value

    @api.model
    def _default_api_key(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].api_key
        return value

    @api.model
    def _default_sign_key(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].sign_key
        return value

    @api.model
    def _default_certification_key(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].certification_key
        return value

    @api.model
    def _default_token(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].token
        return value

    @api.model
    def _default_token_due_date(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].token_due_date
        return value

    @api.model
    def _default_infile_vat(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].infile_vat
        return value

    @api.model
    def _default_certificate_file(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].certificate_file
        return value

    @api.model
    def _default_certificate_password(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].certificate_password
        return value

    @api.model
    def _default_signing_type(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].signing_type
        return value

    @api.model
    def _default_signer_location(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].signer_location
        return value

    @api.model
    def _default_organization_code(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].organization_code
        return value

    @api.model
    def _default_vat_affiliation(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].vat_affiliation
        return value

    @api.model
    def _default_isr_scenery(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].isr_scenery
        return value

    @api.model
    def _default_isr_phrases(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].isr_phrases
        return value

    @api.model
    def _default_excempt_scenery(self):
        value = None
        settings = self.env['infilefel.settings'].search([])
        if settings:
            value = settings[0].excempt_scenery
        return value

    ws_url_token = fields.Char('Token web service URL', default_model='infilefel.config.settings', default=_default_ws_url_token)
    ws_url_document = fields.Char('Document web service URL', default_model='infilefel.config.settings', default=_default_ws_url_document)
    ws_url_void = fields.Char('Void document web service URL', default_model='infilefel.config.settings', default=_default_ws_url_void)
    ws_url_signer = fields.Char('Signer web service URL', default_model='infilefel.config.settings', default = _default_ws_url_signer)
    ws_timeout = fields.Integer('Web service timeout', default_model='infilefel.config.settings', default=_default_ws_timeout)
    user = fields.Char('Certification user', default_model='infilefel.config.settings', default=_default_user)
    sign_user = fields.Char('Sign user', default_model='infilefel.config.settings', default=_default_sign_user)
    api_key = fields.Char('API Key', default_model='infilefel.config.settings', default=_default_api_key)
    sign_key = fields.Char('Sign Key', default_model='infilefel.config.settings', default=_default_sign_key)
    certification_key = fields.Char('Certification Key', default_model='infilefel.config.settings', default=_default_certification_key)
    token = fields.Char('Token', default_model='infilefel.config.settings', default=_default_token)
    token_due_date = fields.Datetime('Token due date', default_model='infilefel.config.settings', default=_default_token_due_date)
    infile_vat = fields.Char('InFile VAT', default_model='infilefel.config.settings', default=_default_infile_vat)
    certificate_file = fields.Char('Certificate file', default_model='infilefel.config.settings', default=_default_certificate_file)
    certificate_password = fields.Char('Certificate password', default_model='infilefel.config.settings', default=_default_certificate_password)
    signing_type = fields.Selection([
        ('LOCAL', 'Sign documents using local program'),
        ('WS', 'Sign documents using Web Service'),
    ], string='Signing type', default_model='infilefel.config.settings', default=_default_signing_type)
    signer_location = fields.Char('Signer program location', default_model='infilefel.config.settings', default=_default_signer_location)
    organization_code = fields.Char('Organization code', default_model='infilefel.config.settings', default=_default_organization_code)
    vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default_model='infilefel.config.settings', default=_default_vat_affiliation)
    isr_scenery = fields.Char('ISR scenery', default_model='infilefel.config.settings', default=_default_isr_scenery)
    isr_phrases = fields.Char('ISR phrases', default_model='infilefel.config.settings', default=_default_isr_phrases)
    excempt_scenery = fields.Char('Excempt scenery', default_model='infilefel.config.settings', default=_default_excempt_scenery)

    @api.multi
    def execute(self):
        ret = super(infilefel_config_settings, self).execute()
        if ret:
            values = {
                'ws_url_token': self.ws_url_token,
                'ws_url_document': self.ws_url_document,
                'ws_url_void': self.ws_url_void,
                'ws_url_signer': self.ws_url_signer,
                'ws_timeout': self.ws_timeout,
                'user': self.user,
                'sign_user': self.sign_user,
                'api_key': self.api_key,
                'sign_key': self.sign_key,
                'certification_key': self.certification_key,
                'token': self.token,
                'token_due_date': self.token_due_date,
                'infile_vat': self.infile_vat,
                'certificate_file': self.certificate_file,
                'certificate_password': self.certificate_password,
                'signing_type': self.signing_type,
                'signer_location': self.signer_location,
                'organization_code': self.organization_code,
                'vat_affiliation': self.vat_affiliation,
                'isr_scenery': self.isr_scenery,
                'isr_phrases': self.isr_phrases,
                'excempt_scenery': self.excempt_scenery,
            }
            settings = self.env['infilefel.settings'].search([])
            if settings:
                settings[0].write(values)
            else:
                settings = self.env['infilefel.settings'].create(values)
        return ret

    @api.multi
    def get_token(self):
        # settings = self.env['infilefel.settings'].search([])
        # if settings:
        #     settings = settings[0]
        #     settings.get_token()
        # else:
        #     raise UserError(_('infilefel: You must first save the settings'))
        if self.ws_url_token:
            if self.user:
                if self.api_key:
                    headers = {
                        'Content-Type': 'application/xml',
                    }
                    data = "<SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>".format(self.user, self.api_key)
                    try:
                        response = requests.post(self.ws_url_token, headers=headers, data=data)
                    except Exception as e:
                        raise UserError(_('infilefel: Error consuming web service: {}').format(e.message))
                    if response:
                        if response.ok:
                            result = xmltodict.parse(response.text)
                            if result['SolicitaTokenResponse']['tipo_respuesta'] == '1':
                                error_message = ''
                                if type(result['SolicitaTokenResponse']['listado_errores']['error']) is list:
                                    for message in result['SolicitaTokenResponse']['listado_errores']['error']:
                                        error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
                                else:
                                    error_message += '\n{}: {}'.format(
                                        result['SolicitaTokenResponse']['listado_errores']['error']['cod_error'],
                                        result['SolicitaTokenResponse']['listado_errores']['error']['desc_error'])
                                raise UserError(_('infilefel Errors {}'.format(error_message)))
                            else:
                                text = ElementTree.fromstring(response.text)
                                token_tag = text.findall('token')
                                if token_tag:
                                    self.token = token_tag[0].text
                                due_date_tag = text.findall('vigencia')
                                if due_date_tag:
                                    # token_due_date = datetime.strptime(due_date_tag[0].text[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone(self.env.user.tz))
                                    token_due_date = datetime.strptime(due_date_tag[0].text[:19], '%Y-%m-%dT%H:%M:%S')
                                    self.token_due_date = token_due_date
                                self.execute()
                else:
                    raise UserError(_('infilefel: API key not set'))
            else:
                raise UserError(_('infilefel: User not set'))
        else:
            raise UserError(_('infilefel: Web service URL for tokens not set'))
