from flask import Flask, request, jsonify

app = Flask(__name__)

# Mapeamento direto de valores para transcrição
mapeamento = {
    "até r$2.800": "Abaixo de R$2.800",
    "maior que r$4.000": "Acima de R$4.000",
    "r$3.500": "Valor específico: R$3.500"
}


# Função para transcrever valores com base no mapeamento
def transcrever_valores(dados):
    sucesso = []
    nao_identificados = []
    logs = []

    for item in dados:
        item_original = item.strip()  # Preserva a versão original do dado
        item_normalizado = item_original.lower().strip()  # Normaliza para comparações
        resultado = mapeamento.get(item_normalizado)

        log_item = {
            "faixa": item_original,
            "status": "Não identificado" if resultado is None else "Identificado",
            "detalhes": "Transcrição realizada com sucesso" if resultado else "Valor não encontrado no mapeamento."
        }

        if resultado:
            sucesso.append(resultado)
        else:
            nao_identificados.append(item_original)

        logs.append(log_item)

    return sucesso, nao_identificados, logs


# Endpoint para transcrever valores
@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", "").split(",")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Transcreve os valores com base no mapeamento
        sucesso, nao_identificados, logs = transcrever_valores(dados)

        return jsonify({
            "sucesso": sucesso,
            "nao_identificados": nao_identificados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao transcrever os valores: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
