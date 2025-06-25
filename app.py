from flask import Flask, render_template, request, jsonify
import json
import os 
from datetime import datetime 

# Certifique-se de que a pasta 'data' existe
if not os.path.exists('data'):
    os.makedirs('data')

# Caminho completo para a pasta templates, caso você ainda esteja usando
# É boa prática incluir static_folder aqui também para garantir que o Flask encontre os arquivos estáticos
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# --- Funções Auxiliares para Respostas Padrão ---
def carregar_respostas():
    try:
        with open('data/respostas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_respostas(respostas):
    with open('data/respostas.json', 'w', encoding='utf-8') as f:
        json.dump(respostas, f, ensure_ascii=False, indent=4)

# --- Funções Auxiliares para Registro de Uso ---
def carregar_uso_respostas():
    try:
        with open('data/uso_respostas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não existir, cria-o com uma lista JSON vazia
        # Isso previne o JSONDecodeError na primeira leitura
        with open('data/uso_respostas.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return [] 

def salvar_uso_respostas(uso_respostas):
    with open('data/uso_respostas.json', 'w', encoding='utf-8') as f:
        json.dump(uso_respostas, f, ensure_ascii=False, indent=4)

# --- Rotas da Aplicação ---
@app.route('/')
def index():
    """Renderiza a página inicial."""
    return render_template('index.html')

@app.route('/respostas')
def gerenciar_respostas():
    """Renderiza a página de gerenciamento de respostas."""
    return render_template('respostas.html')

@app.route('/api/respostas_json', methods=['GET'])
def obter_respostas_json():
    """Retorna a lista de respostas em formato JSON."""
    respostas = carregar_respostas()
    return jsonify(respostas=respostas)

@app.route('/adicionar_resposta', methods=['POST'])
def adicionar_resposta():
    """
    Adiciona uma nova resposta padrão ao arquivo JSON.
    Agora espera dados JSON com 'titulo' e 'texto'.
    """
    data = request.get_json() # Pega os dados JSON da requisição
    titulo = data.get('titulo')
    texto = data.get('texto')

    # Validação básica
    if not titulo or not titulo.strip():
        return jsonify(sucesso=False, mensagem="O título da resposta é obrigatório."), 400
    if not texto or not texto.strip():
        return jsonify(sucesso=False, mensagem="O texto da resposta é obrigatório."), 400

    respostas = carregar_respostas()
    # Pega o maior ID existente e adiciona 1, ou 1 se não houver respostas
    novo_id = max((r['id'] for r in respostas), default=0) + 1
    
    # Adiciona o título e o texto ao dicionário da nova resposta
    respostas.append({'id': novo_id, 'titulo': titulo.strip(), 'texto': texto.strip()})
    salvar_respostas(respostas)
    return jsonify(sucesso=True)

@app.route('/editar_resposta', methods=['POST'])
def editar_resposta():
    """Edita uma resposta existente no arquivo JSON."""
    data = request.get_json()
    id_resposta = data['id']
    novo_texto = data['texto']
    # Opcional: Se quiser editar o título também, adicione novo_titulo = data.get('titulo') aqui
    # e adicione a validação e atualização do título no loop abaixo.

    respostas = carregar_respostas()
    for resposta in respostas:
        if resposta['id'] == id_resposta:
            if novo_texto is not None: # Permite editar apenas o texto
                resposta['texto'] = novo_texto
            # if novo_titulo is not None:
            #     resposta['titulo'] = novo_titulo
            break
    salvar_respostas(respostas)
    return jsonify(sucesso=True)

@app.route('/excluir_resposta', methods=['POST'])
def excluir_resposta():
    """Exclui uma resposta do arquivo JSON e seu histórico de uso."""
    data = request.get_json()
    id_resposta = data['id']
    
    respostas = carregar_respostas()
    # Filtra a lista, removendo a resposta com o ID correspondente
    respostas = [resposta for resposta in respostas if resposta['id'] != id_resposta]
    salvar_respostas(respostas)
    
    # Remove o histórico de uso da resposta excluída para manter os dados limpos
    uso_respostas = carregar_uso_respostas()
    uso_respostas = [uso for uso in uso_respostas if uso['id_resposta'] != id_resposta]
    salvar_uso_respostas(uso_respostas)
    
    return jsonify(sucesso=True)

@app.route('/gerar_resposta')
def pagina_gerar_resposta():
    """Renderiza a página para gerar respostas personalizadas."""
    return render_template('gerar_resposta.html')

@app.route('/registrar_uso', methods=['POST'])
def registrar_uso():
    """Registra o uso de uma resposta."""
    data = request.get_json()
    id_resposta = data['id_resposta']
    
    uso_respostas = carregar_uso_respostas()
    uso_respostas.append({
        'id_resposta': id_resposta,
        'data_uso': datetime.now().isoformat() # Registra a data e hora do uso no formato ISO 8601
    })
    salvar_uso_respostas(uso_respostas)
    return jsonify(sucesso=True)

@app.route('/estatisticas')
def pagina_estatisticas():
    """Renderiza a página de estatísticas de uso."""
    return render_template('estatisticas.html')

@app.route('/api/estatisticas_uso', methods=['GET'])
def obter_estatisticas_uso():
    """Calcula e retorna as estatísticas de uso das respostas."""
    todos_usos = carregar_uso_respostas()
    todas_respostas = carregar_respostas()

    # Cria um dicionário para mapear ID da resposta ao seu título e texto
    mapa_respostas = {resposta['id']: {'titulo': resposta.get('titulo', 'Sem Título'), 'texto': resposta['texto']} for resposta in todas_respostas}

    # Conta a frequência de uso de cada resposta
    frequencia_uso = {}
    for uso in todos_usos:
        id_resp = uso['id_resposta']
        frequencia_uso[id_resp] = frequencia_uso.get(id_resp, 0) + 1

    # Formata os dados para exibição, incluindo o título
    estatisticas = []
    for id_resp, contagem in frequencia_uso.items():
        info_resposta = mapa_respostas.get(id_resp)
        if info_resposta:
            titulo_resposta = info_resposta['titulo']
            texto_completo = info_resposta['texto'] # Mantém o texto completo, se precisar dele em outro lugar
            estatisticas.append({
                'id': id_resp,
                'titulo': titulo_resposta, # Inclui o título
                'contagem': contagem
            })
        else:
            # Caso a resposta tenha sido excluída, mas ainda haja registros de uso
            estatisticas.append({
                'id': id_resp,
                'titulo': f"Resposta ID {id_resp} (Excluída)",
                'contagem': contagem
            })
    
    # Opcional: ordenar por mais usadas primeiro
    estatisticas.sort(key=lambda x: x['contagem'], reverse=True)

    return jsonify(estatisticas=estatisticas)

if __name__ == '__main__':
    # Obtém a porta da variável de ambiente, ou usa 5000 como fallback para desenvolvimento local
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False em produção!