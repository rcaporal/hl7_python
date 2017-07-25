# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2015, CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ALLLLLLLLLLLLLLL
from __future__ import absolute_import
from __future__ import print_function
import uuid
from hl7apy.core import Message, Segment
from hl7apy.parser import parse_message

import re

try:
    from SocketServer import StreamRequestHandler, TCPServer
except ImportError:  # Python 3
    from socketserver import StreamRequestHandler, TCPServer

#: caracteres para codificação MLLP
SB = "\x0b"
EB = "\x1c"
CR = "\x0d"

class MLLProtocol(object):
    """
    Apenas verifica se a mensagem está codificada no seguinte padrão:
    \x0b{conteúdo_da_mensagem}\x1c\x0d
    """
    validator = re.compile(SB + "(([^\r]+\r){1,})" + EB + CR)

    @staticmethod
    def get_message(line):
        message = None
        matched = MLLProtocol.validator.match(line)
        if matched is not None:
            message = matched.groups()[0]
        return message


def responder(m):
    # cria uma mensagem de resposta RSP_K11
    response = Message("RSP_K11")
    response.MSH.MSH_9 = "RSP^K11^RSP_K11"
    response.MSA = "MSA|AA"
    response.MSA.MSA_2 = m.MSH.MSH_10
    qak = Segment("QAK")
    qak.qak_1 = m.QPD.QPD_2
    qak.qak_2 = "OK"
    qak.qak_3 = "Q22^Specimen Labeling Instructions^IHE_LABTF"
    qak.qak_4 = "1"
    response.add(qak)
    response.QPD = m.QPD
    response.PID.PID_1 = '1'
    response.PID.PID_5.PID_5_1 = 'CUNHA'
    response.PID.PID_5.PID_5_2 = 'JOSE'
    response.PID.PID_6 = "19800101"
    response.PID.PID_7 = "F"
    response.PID.PID_23 = "Brasil"
    spm = Segment("SPM")
    obr = Segment("OBR")
    spm.SPM_1 = '1'
    spm.SPM_2 = "12345"
    obr.OBR_4 = "ORDER^DESCRIPTION"
    response.add(spm)
    response.add(obr)
    return response.to_mllp()

class MLLPServer(StreamRequestHandler):
    """
    Simplistic implementation of a TCP server implementing the MLLP protocol
    HL7 messages are encoded between bytes \x0b and \x1c\x0d
    """

    def handle(self):
        line = ''
        while True:
            char = self.rfile.read(1)
            if not char:
                print('Cliente desconectado')
                break
            line += char
            # verifica se existe alguma mensagem HL7 no buffer
            message = MLLProtocol.get_message(line)
            if message is not None:

                try:
                    # parse the incoming message
                    m = parse_message(message, find_groups=False)
                    print("\n=========================================================================")
                    print("Mensagem recebida com sucesso")
                    print("\nTipo da Mensagem Recebida: ", m.MSH.message_type.to_er7())
                    print("\nMensagem Recebida de: ", m.MSH.sending_application.to_er7())
                    print("\nConteudo da mensagem:", repr(m.to_er7()))
                    print("\n=========================================================================")
                except:
                    print("Falha no Parsing!", repr(message))

                if m.MSH.MSH_9.MSH_9_3.to_er7() == 'QBP_Q11':
                    response = responder(m)
                else:
                    print ("Mensagem recebida irregularmente!")
                    response = "none"

                self.wfile.write(response)
                line = ''

if __name__ == "__main__":
    HOST, PORT = "localhost", 6000

    server = TCPServer((HOST, PORT), MLLPServer)
    server.serve_forever()
