from flask import Flask, request, jsonify
import re

app = Flask(__name__)

def gerar_regex_automatico(valores):
    """
    Gera regex dinamicamente com base nos valores recebidos.
    """
    faixas = {}
    for valor in valores:
        valor_limpo = re.sub(r'[^\w\s,.R$]', '', valor.lower().strip())
        valor_limpo = re.sub(r'[.,]', '', valor_limpo)
        
        # Identificar padrões numéricos e criar regex apropriado
        if "abaixo de" in valor_limpo or "até" in valor_limpo or "menor que" in valor_limpo:
            limite = re.search(r'\d+', valor_limpo)
            if limite:
                regex = rf"(abaixo_de|ate|menor_que|menor).*{limite.group(0)}"
                faixas[regex] = f"Abaixo de R${limite.group(0)}"

        elif "entre" in valor_limpo:
            limites = re.findall(r'\d+', valor_limpo)
            if len(limites) == 2:
                regex = rf"(entre).*{limites[0]}.*{limites[1]}"
                faixas[regex] = f"Entre R${limites[0]} e R${limites[1]}"

        elif "acima de" in valor_limpo or "maior que" in valor_limpo:
            limite = re.search(r'\d+', valor_limpo)
            if limite:
                regex = rf"(acima_de|maior_que|maior).*{limite.group(0)}"
                faixas[regex] = f"Acima de R${limite.group(0)}"

        else:
            numeros = re.findall(r'\d+', valor_limpo)
            if len(numeros) == 1:
                regex = rf".*{numeros[0]}.*"
                faixas[regex] = f"Contém o valor R${numeros[0]}"

    return faixas


def limpar_e_mapear(valor, faixas):
    """
    Limpa o valor e aplica o regex gerado dinamicamente.
    """
    valor = re.sub(r'[^\w\s,.R$]', '', valor.lower().strip())
    valor = re.sub(r'[.,]', '', valor)  # Remove pontuações problemáticas
    for padrao, faixa in faixas.items():
        if re.search(padrao, valor):
            return faixa
    return "Faixa não identificada"


@app.route('/process', methods=['POST'])
def processar_dados_em_massa():
    """
    Endpoint que processa os dados em massa com regex automático.
    """
    entrada = request.json.get("dados", [])
    if not isinstance(entrada, list) or len(entrada) == 0 or not isinstance(entrada[0], str):
        return jsonify({"error": "Esperado um array contendo uma única string no campo 'dados'"}), 400
    
    # Separar os valores enviados em uma lista
    valores = entrada[0].split(',')
    
    # Gerar regex automático com base nos valores
    faixas = gerar_regex_automatico(valores)
    
    # Processar os valores
    faixas_padronizadas = []
    for valor in valores:
        faixa = limpar_e_mapear(valor, faixas)
        faixas_padronizadas.append(faixa)
    
    # Retornar apenas os dados padronizados, separados por vírgula
    return jsonify(", ".join(faixas_padronizadas))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
