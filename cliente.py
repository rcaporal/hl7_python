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

from __future__ import absolute_import
import socket
import uuid

from hl7apy.core import Message
from hl7apy.parser import parse_message
from servidor import MLLProtocol


def enviar(patient_id):
    # cria uma mensagem de consulta QBP_Q11 de acordo com o id do paciente
    m = Message("QBP_Q11")
    m.MSH.sending_application = "Cliente"
    m.MSH.receiving_application = "Servidor"
    m.MSH.MSH_9 = "QBP^SLI^QBP_Q11"
    m.MSH.MSH_10 = uuid.uuid4().hex
    m.QPD.QPD_1 = "SLI^Specimen Labeling Instructions^IHE_LABTF"
    m.QPD.query_tag = uuid.uuid4().hex
    m.QPD.QPD_3 = patient_id
    m.RCP = "RCP|I||R"
    return m.to_mllp()

def query(host, port, patient_id):
    """
    Estabelecer uma conecção TCP utilizando como parâmetros o endereço e a porta do
    servidor para enviar uma mensagem de exemplo QBP_Q11
    :param host: endereço para conexão
    :param port: porta para conexão
    :param patient_id: patient_id para a mensgem de consulta
    """
    # gerando a mensagem QBP_Q11
    pacote = enviar(patient_id)

    # estabelecendo conexão
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        # enviar a mensagem
        sock.sendall(pacote)

        # receber a resposta
        received = sock.recv(1024*1024)
        mensagem = MLLProtocol.get_message(received)

        # manipular a resposta

        try:
            # parse the incoming HL7 message
            m = parse_message(mensagem, find_groups=False)
        except:
            print 'parsing failed', repr(mensagem)
        else:
            print "\n========================================================================="
            print "Resposta do Servidor:\n\n"
            print "\nTipo da Mensagem Recebida: ", m.MSH.message_type.to_er7()
            print "\nID do paciente: ", m.PID.PID_1.to_er7()
            print "\nNome do paciente: ", m.PID.PID_5.given_name.to_er7(), m.PID.PID_5.family_name.to_er7()
            ano = m.PID.PID_6.to_er7()
            print "\nAno de nascimento: ", ano[0:4]
            print "\nLocal de nascimento: ", m.PID.PID_23.to_er7()
            print "\nConteudo da mensagem: ", repr(m.to_er7())
            print "\n========================================================================="

    finally:
        sock.close()

if __name__ == '__main__':
    host, port = 'localhost', 6000
    patient_id = '100002'
    query(host, port, patient_id)
