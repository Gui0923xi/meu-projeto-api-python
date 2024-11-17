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

            # Trata underscores e troca por espaços
            item = item.replace("_", " ")

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


# Função para transcrever diretamente
def transcrever_dados(dados_lista):
    transcricoes = {}
    logs = []

    for item in dados_lista:
        log_item = {"faixa": item, "status": "", "detalhes": ""}
        try:
            item = item.lower().strip()

            # Ajusta underscores e converte diretamente
            item = item.replace("_", " ")

            if item.startswith("até"):
                transcricoes[item] = item.replace("até", "Abaixo de").capitalize()
                log_item["status"] = "Transcrito"
                log_item["detalhes"] = "Transcrição direta realizada."

            elif "maior que" in item:
                transcricoes[item] = item.replace("maior que", "Acima de").capitalize()
                log_item["status"] = "Transcrito"
                log_item["detalhes"] = "Transcrição direta realizada."

            elif "r$" in item:
                transcricoes[item] = f"Abaixo de R${item.replace('r$', '').strip()}"
                log_item["status"] = "Transcrito"
                log_item["detalhes"] = "Valor específico transcrito."

            else:
                log_item["status"] = "Não identificado"
                log_item["detalhes"] = "Nenhum padrão aplicável para transcrição."

        except Exception as e:
            log_item["status"] = "Erro"
            log_item["detalhes"] = f"Erro ao transcrever: {str(e)}"

        logs.append(log_item)

    return transcricoes, logs


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
        logs = []

        for item in dados:
            item = item.strip()
            identificado = False

            for padrao, descricao in regex.items():
                if re.search(padrao, item):
                    sucesso.append(descricao)
                    identificado = True
                    break

            if not identificado:
                nao_identificados.append(item)

        # Transcrever os não identificados como fallback
        transcricoes, transcricao_logs = transcrever_dados(nao_identificados)
        sucesso.extend(transcricoes.values())
        logs.extend(transcricao_logs)

        return jsonify({"sucesso": sucesso, "nao_identificados": nao_identificados, "logs": logs}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar: {str(e)}"}), 500


@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        dados = request.json.get("dados", "").split(",")
        transcricoes, logs = transcrever_dados(dados)
        return jsonify({"transcricoes": transcricoes, "logs": logs}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao transcrever: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
