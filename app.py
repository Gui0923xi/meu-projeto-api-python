from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Regex gerados dinamicamente
regex_map = {}

# Função para limpar os dados
def limpar_dados(dados):
    dados_limpos = []
    for dado in dados:
        dado = dado.strip().lower()  # Remove espaços e normaliza para lowercase
        dado = re.sub(r"[^\w\s.,$]", "", dado)  # Remove caracteres inválidos
        dado = re.sub(r"\s+", " ", dado)  # Normaliza espaços múltiplos
        dados_limpos.append(dado)
    return dados_limpos

# Função para gerar regex dinamicamente
def gerar_regex(dados):
    global regex_map
    regex_map = {}  # Limpa o mapa de regex antes de gerar novos
    logs = []  # Logs para cada faixa processada

    for item in dados:
        log_item = {"faixa": item, "status": "Não processada", "detalhes": ""}

        # Substituir underscores por espaços para compatibilidade
        item = item.replace("_", " ")

        # Faixas como "Entre R$X e R$Y" ou "R$X_a_R$Y"
        if re.search(r"(entre|de)\s*r\$\s?[0-9]+[.,]?[0-9]*\s*(e|a)\s*r\$\s?[0-9]+[.,]?[0-9]*", item) or "_a_" in item:
            match = re.findall(r"r\$\s?([0-9]+[.,]?[0-9]*)_a_r\$\s?([0-9]+[.,]?[0-9]*)", item) or \
                    re.findall(r"r\$\s?([0-9]+[.,]?[0-9]*)\s*(e|a)\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                valor1, valor2 = m[0], m[1]
                regex_key = rf"r\$\s?{re.escape(valor1)}.*(e|a).*r\$\s?{re.escape(valor2)}"
                regex_map[regex_key] = f"Entre R${valor1} e R${valor2}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Até R$X"
        elif re.search(r"até\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"até\s*r\$\s?{re.escape(m)}"
                regex_map[regex_key] = f"Abaixo de R${m}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "De R$X"
        elif re.search(r"de\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"de\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"de\s*r\$\s?{re.escape(m)}"
                regex_map[regex_key] = f"Acima de R${m}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Maior que R$X"
        elif re.search(r"(maior|acima)\s*que\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(maior|acima)\s*que\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"(maior|acima)\s*que\s*r\$\s?{re.escape(m[1])}"
                regex_map[regex_key] = f"Acima de R${m[1]}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        else:
            log_item["detalhes"] = "Nenhum padrão conhecido foi encontrado."

        logs.append(log_item)

    return regex_map, logs

# Outros endpoints permanecem os mesmos
@app.route('/update-regex', methods=['POST'])
def update_regex():
    # Código do endpoint...
    pass

# Resto da API

if __name__ == '__main__':
    app.run(debug=True)
