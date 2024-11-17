from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados_lista):
    regex_gerados = {}
    logs = []

    for item in dados_lista:
        log_item = {"faixa": item, "status": "", "detalhes": ""}
        try:
            item = item.lower().strip()  # Normaliza o texto para evitar erros
            item = item.replace("_", " ")  # Substitui underscores por espaços

            # Faixas como "Entre R$X e R$Y" ou "R$X_a_R$Y"
            if re.search(r"r\$[0-9]+[.,]?[0-9]*\s*(a|e)\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"r\$([0-9]+[.,]?[0-9]*)\s*(a|e)\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    valor1, valor2 = m[0], m[2]
                    regex_key = rf"r\$?{re.escape(valor1)}.*(a|e).*r\$?{re.escape(valor2)}"
                    regex_gerados[regex_key] = f"Entre R${valor1} e R${valor2}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Até R$X" -> "Abaixo de R$X"
            elif re.search(r"até\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"até\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"até\s*r\$?{re.escape(m)}"
                    regex_gerados[regex_key] = f"Abaixo de R${m}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Maior que R$X" -> "Acima de R$X"
            elif re.search(r"(maior|acima)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"(maior|acima)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"(maior|acima)\s*que\s*r\$?{re.escape(m[1])}"
                    regex_gerados[regex_key] = f"Acima de R${m[1]}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Menor que R$X" -> "Abaixo de R$X"
            elif re.search(r"(menor|abaixo)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"(menor|abaixo)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"(menor|abaixo)\s*que\s*r\$?{re.escape(m[1])}"
                    regex_gerados[regex_key] = f"Abaixo de R${m[1]}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # Casos restantes: "R$X" ou outros
            elif re.match(r"^r\$[0-9]+[.,]?[0-9]*$", item):
                valor = item.replace("r$", "")
                regex_key = rf"r\$?{re.escape(valor)}"
                regex_gerados[regex_key] = f"Abaixo de R${valor}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

            else:
                log_item["status"] = "Não identificado"
                log_item["detalhes"] = "Faixa não corresponde a nenhum padrão conhecido."

        except Exception as e:
            log_item["status"] = "Erro"
            log_item["detalhes"] = f"Erro ao processar: {str(e)}"

        logs.append(log_item)

    return regex_gerados, logs


# Função de transcrição direta
def transcrever_dados(dados_lista):
    transcritos = {}
    logs = []

    for item in dados_lista:
        log_item = {"faixa": item, "status": "", "detalhes": ""}
        try:
            item = item.lower().strip()

            # Transcrição direta para valores específicos
            if re.match(r"^r\$[0-9]+[.,]?[0-9]*$", item):
                valor = item.replace("r$", "")
                transcritos[item] = f"Abaixo de R${valor}"
                log_item["status"] = "Transcrito"
                log_item["detalhes"] = "Valor específico transcrito."

            # Transcrição direta para outros casos
            else:
                transcritos[item] = f"Transcrição direta de '{item}'"
                log_item["status"] = "Transcrito"
                log_item["detalhes"] = "Transcrição direta realizada."

        except Exception as e:
            log_item["status"] = "Erro"
            log_item["detalhes"] = f"Erro ao transcrever: {str(e)}"

        logs.append(log_item)

    return transcritos, logs


@app.route('/update-regex', methods=['POST'])
def update_regex():
    try:
        dados = request.json.get("dados", "").split(",")
        regex_gerados, logs = gerar_regex(dados)
        return jsonify({"regex": regex_gerados, "logs": logs}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500


@app.route('/process', methods=['POST'])
def process():
    try:
        dados = request.json.get("dados", "").split(",")
        regex = request.json.get("regex", {})

        sucesso = []
        nao_identificados = []

        for item in dados:
            identificado = False
            for padrao, descricao in regex.items():
                if re.search(padrao, item):
                    sucesso.append(descricao)
                    identificado = True
                    break
            if not identificado:
                nao_identificados.append(item)

        return jsonify({"sucesso": sucesso, "nao_identificados": nao_identificados}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500


@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        dados = request.json.get("dados", "").split(",")
        transcritos, logs = transcrever_dados(dados)
        return jsonify({"transcritos": transcritos, "logs": logs}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao transcrever os dados: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
