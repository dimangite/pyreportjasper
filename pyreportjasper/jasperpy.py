# -*- coding: utf-8 -*-
# GNU GENERAL PUBLIC LICENSE
#
# Copyright (c) 2020 Jadson Bonfim Ribeiro <contato@jadsonbr.com.br>
#

import os
import jpyutil
import jpy
from requests import Request, Session
import tempfile
import json
import glob


class JasperPy:

    _FORMATS = (
        'pdf',
        'rtf',
        'xls',
        'xlsx',
        'docx',
        'odt',
        'ods',
        'pptx',
        'csv',
        'html',
        'xhtml',
        'xml',
        'jrprint',
    )

    _FORMATS_JSON = ('pdf')

    _FORMATS_METHODS_REQUEST = ('GET', 'POST', 'PUT')

    def __init__(self, jvm_maxmem='512M', jvm_classpath=None):
        self.WINDOWS = True if os.name == 'nt' else False
        self.SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
        self.LIBS = os.path.join(self.SCRIPT_DIR, 'jasperstarter', 'lib')
        self.JDBC_DIR = os.path.join(self.SCRIPT_DIR, 'jasperstarter', 'jdbc')
        self.JDBC_FILE = os.path.join(self.SCRIPT_DIR, 'jasperstarter', 'jdbc', 'postgresql.jar')
        if not os.path.isdir(self.LIBS):
            raise NameError('Unable to find lib in {0}'.format(self.LIBS))
        self.CLASSPATH = os.path.join(self.LIBS, 'jasperstarter.jar')
        if not os.path.exists(self.CLASSPATH):
            raise NameError('Unable to find jasperstarter in {0}'.format(self.LIBS))
        if jvm_classpath is None:
            jpyutil.init_jvm(jvm_maxmem=jvm_maxmem, jvm_classpath=[self.CLASSPATH])
        else:
            jpyutil.init_jvm(jvm_maxmem=jvm_maxmem, jvm_classpath=[jvm_classpath])

        self.jvArrays = jpy.get_type('java.util.Arrays')
        self.jvFile = jpy.get_type('java.io.File')
        self.jvReport = jpy.get_type('de.cenote.jasperstarter.Report')
        self.jvConfig = jpy.get_type('de.cenote.jasperstarter.Config')
        self.jvDsType = jpy.get_type('de.cenote.jasperstarter.types.DsType')
        self.jvSystem = jpy.get_type('java.lang.System')
        self.jvPrintStream = jpy.get_type('java.io.PrintStream')
        self.jvByteArrayInputStream = jpy.get_type('java.io.ByteArrayInputStream')
        self.jvByteArrayOutputStream = jpy.get_type('java.io.ByteArrayOutputStream')
        self.jvApplicationClasspath = jpy.get_type('de.cenote.tools.classpath.ApplicationClasspath')

        self.jvHashMap = jpy.get_type('java.util.HashMap')
        self.jvLocale = jpy.get_type('java.util.Locale')
        self.jvJasperFillManager = jpy.get_type('net.sf.jasperreports.engine.JasperFillManager')
        self.jvJRParameter = jpy.get_type('net.sf.jasperreports.engine.JRParameter')
        self.jvJREmptyDataSource = jpy.get_type('net.sf.jasperreports.engine.JREmptyDataSource')
        self.jvDb = jpy.get_type('de.cenote.jasperstarter.Db')
        self.jvJsonQueryExecuterFactory = jpy.get_type('net.sf.jasperreports.engine.query.JsonQueryExecuterFactory')
        self.jvJasperExportManager = jpy.get_type('net.sf.jasperreports.engine.JasperExportManager')

    def compile(self, report):
        """
        Compile .jrxml to .jasper file
        :param report:      The name of the report .jrxml.
        """

        if not report:
            raise NameError('No input file!')

        try:
            try:
                config = self.jvConfig()
                config.setInput(report)
                report = self.jvReport(config, self.jvFile(config.getInput()))
                report.compileToFile()
            finally:
                self.jvSystem.out.flush()

            return 0
        except Exception as e:
            raise NameError('Error: %s' % str(e))

    def process(self, input_file, output_file=False, format_list=['pdf'],
                parameters={}, db_connection={}, locale='pt_BR', resource=""):
        """
        Generate PDF from a report file

        :param input_file:      The name of the report .jrxml.
        :param output_file:     Destination File.
        :param format_list:     List of Output File Types (Ex: ['pdf', 'xls'])
        :param parameters:      Settings for the report in the form of a dictionary
                                where the values are the string representations (in
                                Java format, so Python's True is 'true').
        :param db_connection:   Data to connect to the database.
        :param locale:          Language Locations
        :param resource:        Use features like (i18n resource bundles, icons or images).

        :return: a int.
        """

        if not input_file:
            raise NameError('No input file!')

        if isinstance(format_list, list):
            if any([key not in self._FORMATS for key in format_list]):
                raise NameError('Invalid format!')
        else:
            raise NameError("'format_list' value is not list!")

        try:
            config = self.jvConfig()
            config.setInput(input_file)
            config.setLocale(locale)
            if output_file:
                config.setOutput(output_file)
            else:
                config.setOutput(os.path.dirname(input_file))
            config.setOutputFormats(self.jvArrays.asList(format_list))
            if len(parameters) > 0:
                config.setParams(self.jvArrays.asList([k + '=' + v for k, v in parameters.items()]))
            if 'driver' in db_connection:
                if db_connection['driver'] == 'postgres':
                    config.setDbType(self.jvDsType.postgres)
                elif db_connection['driver'] == 'mysql':
                    config.setDbType(self.jvDsType.mysql)
                elif db_connection['driver'] == 'oracle':
                    config.setDbType(self.jvDsType.oracle)
                elif db_connection['driver'] == 'generic':
                    config.setDbType(self.jvDsType.generic)
                elif db_connection['driver'] == 'csv':
                    config.setDbType(self.jvDsType.csv)
                elif db_connection['driver'] == 'xml':
                    config.setDbType(self.jvDsType.xml)
                elif db_connection['driver'] == 'json':
                    config.setDbType(self.jvDsType.json)
                elif db_connection['driver'] == 'jsonql':
                    config.setDbType(self.jvDsType.jsonql)
            else:
                config.setDbType(self.jvDsType.none)

            if len(db_connection) > 0:
                if 'username' in db_connection:
                    config.setDbUser(db_connection['username'])

                if 'password' in db_connection:
                    config.setDbPasswd(db_connection['password'])

                if 'host' in db_connection:
                    config.setDbHost(db_connection['host'])

                if 'database' in db_connection:
                    config.setDbName(db_connection['database'])

                if 'port' in db_connection:
                    config.setDbPort(int(db_connection['port']))

                if 'jdbc_dir' in db_connection:
                    config.setJdbcDir(self.jvFile(db_connection['jdbc_dir']))

                if 'db_sid' in db_connection:
                    config.setDbSid(db_connection['db_sid'])

                if 'xml_xpath' in db_connection:
                    config.setXmlXpath(db_connection['xml_xpath'])

                if 'data_file' in db_connection:
                    config.setDataFile(self.jvFile(db_connection['data_file']))

                if 'json_query' in db_connection:
                    config.setJsonQuery(db_connection['json_query'])

                if 'jsonql_query' in db_connection:
                    config.setJsonQLQuery(db_connection['jsonql_query'])

                if 'csv_first_row' in db_connection:
                    config.setCsvFirstRow(True)

                if 'csv_columns' in db_connection:
                    config.setCsvColumns(db_connection['csv_columns'])

                if 'csv_record_del' in db_connection:
                    config.setCsvRecordDel(db_connection['csv_record_del'])

                if 'csv_field_del' in db_connection:
                    config.setCsvFieldDel(db_connection['csv_field_del'])

                if 'csv_charset' in db_connection:
                    config.setCsvCharset(db_connection['csv_charset'])

            self.jvApplicationClasspath.add(self.jvFile(self.JDBC_FILE))

            if os.path.isfile(resource):
                self.jvApplicationClasspath.add(self.jvFile(resource))
                # self.jvApplicationClasspath.add(os.path.dirname(resource))
            elif os.path.isdir(resource):
                self.jvApplicationClasspath.add(resource)
                for res_file in glob.glob(os.path.join(resource, '*.jar')):
                    self.jvApplicationClasspath.add(self.jvFile(res_file))

            #
            # Run the report. See Report.java for details.
            #
            report = self.jvReport(config, self.jvFile(config.getInput()))
            savedStdin = getattr(self.jvSystem, 'in')
            savedStdout = self.jvSystem.out
            tmpStdout = self.jvByteArrayOutputStream()
            try:
                self.jvSystem.setOut(self.jvPrintStream(tmpStdout))
                report.fill()
                for format_out in format_list:
                    if format_out == 'pdf':
                        report.exportPdf()
                    elif format_out == 'rtf':
                        report.exportRtf()
                    elif format_out == 'xls':
                        report.exportXls()
                    elif format_out == 'xlsx':
                        report.exportXlsx()
                    elif format_out == 'docx':
                        report.exportDocx()
                    elif format_out == 'odt':
                        report.exportOdt()
                    elif format_out == 'ods':
                        report.exportOds()
                    elif format_out == 'pptx':
                        report.exportPptx()
                    elif format_out == 'csv':
                        report.exportCsv()
                    elif format_out == 'html':
                        report.exportHtml()
                    elif format_out == 'xhtml':
                        report.exportXhtml()
                    elif format_out == 'xml':
                        report.exportXml()
                    elif format_out == 'jrprint':
                        report.exportJrprint()
                    else:
                        raise NameError("Error output format \"" + format_out + "\" not implemented!")
            finally:
                self.jvSystem.out.flush()
                self.jvSystem.setIn(savedStdin)
                self.jvSystem.setOut(savedStdout)
            #
            # Emit PDF.
            #
            return 0

        except Exception as e:
            raise NameError('Error: %s' % str(e))


    def process_json(self, input_file, output_file=False, format_list=['pdf'],
                parameters={}, connection={}, locale=False, resource=""):

        with tempfile.TemporaryDirectory() as tmp_dir:
            if not input_file:
                raise NameError('No input file!')

            if isinstance(format_list, list):
                if any([key not in self._FORMATS_JSON for key in format_list]):
                    raise NameError('Invalid format output!')
            else:
                raise NameError("'format_list' value is not list!")

            try:
                config = self.jvConfig()
                config.setInput(input_file)
                if locale:
                    config.setLocale(locale)
                if output_file:
                    config.setOutput(output_file)
                else:
                    list_patch = input_file.split('/')
                    list_name_extesion = list_patch[-1].split('.')
                    name_file = list_name_extesion[0]
                    file_out = os.path.join(os.path.dirname(input_file), name_file + '.jasper')
                    output_file = os.path.join(os.path.dirname(input_file), name_file + '.pdf')
                    config.setOutput(os.path.dirname(input_file))
                config.setOutputFormats(self.jvArrays.asList(format_list))
                if len(parameters) > 0:
                    config.setParams(self.jvArrays.asList([k + '=' + v for k, v in parameters.items()]))
                if 'driver' in connection:
                    if connection['driver'] == 'json':
                        config.setDbType(self.jvDsType.json)
                    elif connection['driver'] == 'jsonql':
                        config.setDbType(self.jvDsType.jsonql)
                else:
                    config.setDbType(self.jvDsType.none)

                if len(connection) > 0:
                    if 'data_file' not in connection and 'url_file' not in connection:
                        raise NameError('No data sources were reported')

                    if 'data_file' in connection:
                        config.setDataFile(self.jvFile(connection['data_file']))

                    if 'url_file' in connection:
                        try:
                            if isinstance(connection['url_method'], str):
                                if connection['url_method'] not in self._FORMATS_METHODS_REQUEST:
                                    raise NameError('Invalid method request!')
                            else:
                                raise NameError("'url_method' value is not list!")

                            PARAMS = connection['url_params'] if 'url_params' in connection else {}
                            DATA = connection['url_data'] if 'url_data_post' in connection else {}
                            HEADER = connection['url_header'] if 'url_header' in connection else {}

                            if 'url_method' in connection:
                                s = Session()
                                prepped = Request(
                                    connection['url_method'],
                                    connection['url_file'],
                                    data=DATA,
                                    headers=HEADER,
                                    params=PARAMS
                                ).prepare()
                                resp = s.send(request=prepped)
                            if resp.status_code == 200:
                                data = resp.json()
                                file_json = os.path.join(tmp_dir, 'data_report.json')
                                with open(file_json, 'w') as file:
                                    file.write(json.dumps(data))
                                config.setDataFile(self.jvFile(file_json))
                            else:
                                raise NameError('Error request status code: %s' % str(resp.status_code))
                        except Exception as e:
                            raise NameError('Error request: %s' % str(e))

                    if 'json_query' in connection:
                        config.setJsonQuery(connection['json_query'])

                    if 'jsonql_query' in connection:
                        config.setJsonQLQuery(connection['jsonql_query'])

                if os.path.isfile(resource):
                    self.jvApplicationClasspath.add(os.path.dirname(resource))
                elif os.path.isdir(resource):
                    self.jvApplicationClasspath.add(resource)

                report = self.jvReport(config, self.jvFile(config.getInput()))
                self.compile(input_file)
                parameters = self.jvHashMap()
                if config.hasAskFilter():
                    reportParams = config.getParams()
                    parameters = report.promptForParams(reportParams, parameters, report.jasperReport.getName());
                try:
                    if self.jvDsType.jsonql.equals(config.getDbType()):
                        db = self.jvDb()
                        ds = db.getJsonQLDataSource(config)
                        if 'json_locale' in connection:
                            parameters.put(self.jvJsonQueryExecuterFactory.JSON_LOCALE,
                                           self.jvLocale(connection['json_locale']))

                        if 'json_date_pattern' in connection:
                            parameters.put(self.jvJsonQueryExecuterFactory.JSON_DATE_PATTERN,
                                           self.jvLocale(connection['json_date_pattern']))

                        if 'json_number_pattern' in connection:
                            parameters.put(self.jvJsonQueryExecuterFactory.JSON_NUMBER_PATTERN,
                                           self.jvLocale(connection['json_number_pattern']))

                        if 'json_time_zone' in connection:
                            parameters.put(self.jvJsonQueryExecuterFactory.JSON_TIME_ZONE,
                                           self.jvLocale(connection['json_time_zone']))

                        jasperPrint = self.jvJasperFillManager.fillReport(file_out, parameters, ds)
                        self.jvJasperExportManager.exportReportToPdfFile(jasperPrint, output_file)
                    else:
                        raise NameError('Invalid json input!')
                except Exception as e:
                    raise NameError('Error: %s' % str(e))

                return 0
            except Exception as e:
                raise NameError('Error: %s' % str(e))