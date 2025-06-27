from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

# Certifique-se de que a pasta 'data' existe
if not os.path.exists('data'):
    os.makedirs('data')

# Caminho completo para a pasta templates e static
# É boa prática incluir static_folder aqui também para garantir que o Flask encontre os arquivos estáticos
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# --- Funções Auxiliares para Respostas Padrão ---
def carregar_respostas():
    """
    Carrega as respostas do arquivo JSON, desempacotando-as de sua nova estrutura por tema.
    Retorna uma lista plana de todas as respostas, com a categoria atribuída.
    """
    try:
        with open('data/respostas.json', 'r', encoding='utf-8') as f:
            # O JSON agora é uma lista de objetos de tema, cada um com uma lista de respostas
            temas_com_respostas = json.load(f)
            
            todas_respostas_planas = []
            for tema_obj in temas_com_respostas:
                # Pega o nome do tema para usar como categoria para as respostas dentro dele
                tema_nome = tema_obj.get("tema", "Sem Categoria") 
                
                # Itera sobre a lista de respostas dentro de cada tema
                for resposta in tema_obj.get("respostas", []):
                    # Adiciona a categoria à resposta. Se a resposta já tiver uma categoria,
                    # esta linha irá sobrescrevê-la com o nome do tema, garantindo consistência.
                    resposta["categoria"] = tema_nome 
                    todas_respostas_planas.append(resposta)
            
            # Ordena a lista plana de respostas pelo ID antes de retornar
            # Isso garante que o dropdown e a tabela exibam os itens em ordem numérica.
            todas_respostas_planas.sort(key=lambda r: r['id'])
            
            return todas_respostas_planas
    except FileNotFoundError:
        # Se o arquivo não for encontrado, retorna uma lista vazia
        print("Arquivo respostas.json não encontrado. Retornando lista vazia.")
        return []
    except json.JSONDecodeError as e:
        # Se o JSON estiver malformado, imprime o erro e retorna uma lista vazia
        print(f"Erro ao decodificar JSON em respostas.json: {e}")
        return []

def salvar_respostas(respostas):
    """
    Salva as respostas no arquivo JSON.
    NOTA IMPORTANTE: Esta função salva uma lista PLANA de respostas.
    A estrutura de categorias (temas) no JSON original não será mantida
    se você adicionar ou editar respostas via interface web, pois o Flask
    opera com a lista plana. Para manter a estrutura aninhada, esta função
    precisaria de uma lógica mais complexa para reagrupar as respostas por
    categoria antes de salvar.
    """
    with open('data/respostas.json', 'w', encoding='utf-8') as f:
        json.dump(respostas, f, ensure_ascii=False, indent=4)

# --- Funções Auxiliares para Registro de Uso ---
def carregar_uso_respostas():
    """Carrega o histórico de uso das respostas do arquivo JSON."""
    try:
        with open('data/uso_respostas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não existir, cria-o com uma lista JSON vazia
        with open('data/uso_respostas.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return []

def salvar_uso_respostas(uso_respostas):
    """Salva o histórico de uso das respostas no arquivo JSON."""
    with open('data/uso_respostas.json', 'w', encoding='utf-8') as f:
        json.dump(uso_respostas, f, ensure_ascii=False, indent=4)

# --- Função Auxiliar para Saudação Dinâmica ---
def obter_saudacao():
    """Retorna 'Bom dia', 'Boa tarde' ou 'Boa noite' baseado na hora atual no fuso horário local."""
    hora_atual = datetime.now().hour
    if 6 <= hora_atual < 12:
        return "Bom dia"
    elif 12 <= hora_atual < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

# --- Rotas da Aplicação ---
@app.route('/')
def index():
    """Renderiza a página inicial com saudação dinâmica."""
    saudacao = obter_saudacao()
    return render_template('index.html', saudacao=saudacao)

@app.route('/respostas')
def gerenciar_respostas():
    """Renderiza a página de gerenciamento de respostas."""
    return render_template('respostas.html')

@app.route('/api/respostas_json', methods=['GET'])
def obter_respostas_json():
    """Retorna a lista de respostas em formato JSON, com categorias."""
    respostas = carregar_respostas() # Esta função agora retorna uma lista plana com a categoria
    return jsonify(respostas=respostas)

@app.route('/adicionar_resposta', methods=['POST'])
def adicionar_resposta():
    """
    Adiciona uma nova resposta padrão ao arquivo JSON.
    Espera dados JSON com 'titulo' e 'texto'.
    """
    data = request.get_json()
    titulo = data.get('titulo')
    texto = data.get('texto')

    if not titulo or not titulo.strip():
        return jsonify(sucesso=False, mensagem="O título da resposta é obrigatório."), 400
    if not texto or not texto.strip():
        return jsonify(sucesso=False, mensagem="O texto da resposta é obrigatório."), 400

    respostas = carregar_respostas()
    novo_id = max((r['id'] for r in respostas), default=0) + 1

    # Ao adicionar uma nova resposta, ela será colocada em uma categoria padrão.
    # Se você quiser que o usuário escolha a categoria, precisaria de um campo de input para isso no frontend.
    respostas.append({'id': novo_id, 'titulo': titulo.strip(), 'texto': texto.strip(), 'categoria': 'Adicionadas Manualmente'})
    salvar_respostas(respostas)
    return jsonify(sucesso=True)

@app.route('/editar_resposta', methods=['POST'])
def editar_resposta():
    """Edita uma resposta existente no arquivo JSON."""
    data = request.get_json()
    id_resposta = data['id']
    novo_texto = data['texto']
    # Para editar o título e/ou a categoria também, você precisaria adicionar
    # os campos correspondentes no JSON enviado pelo frontend e atualizar aqui.

    respostas = carregar_respostas()
    for resposta in respostas:
        if resposta['id'] == id_resposta:
            if novo_texto is not None:
                resposta['texto'] = novo_texto
            # if 'novo_titulo' in data:
            #     resposta['titulo'] = data['novo_titulo']
            # if 'nova_categoria' in data:
            #     resposta['categoria'] = data['nova_categoria']
            break
    salvar_respostas(respostas)
    return jsonify(sucesso=True)

@app.route('/excluir_resposta', methods=['POST'])
def excluir_resposta():
    """Exclui uma resposta do arquivo JSON e seu histórico de uso."""
    data = request.get_json()
    id_resposta = data['id']

    respostas = carregar_respostas()
    respostas = [resposta for resposta in respostas if resposta['id'] != id_resposta]
    salvar_respostas(respostas)

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
        'data_uso': datetime.now().isoformat()
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
    todas_respostas = carregar_respostas() # Já retorna lista plana com categoria

    mapa_respostas = {resposta['id']: {'titulo': resposta.get('titulo', 'Sem Título'), 'categoria': resposta.get('categoria', 'Sem Categoria')} for resposta in todas_respostas}

    frequencia_uso = {}
    for uso in todos_usos:
        id_resp = uso['id_resposta']
        frequencia_uso[id_resp] = frequencia_uso.get(id_resp, 0) + 1

    estatisticas = []
    for id_resp, contagem in frequencia_uso.items():
        info_resposta = mapa_respostas.get(id_resp)
        if info_resposta:
            titulo_resposta = info_resposta['titulo']
            categoria_resposta = info_resposta['categoria'] # Adiciona a categoria aqui
            estatisticas.append({
                'id': id_resp,
                'titulo': titulo_resposta,
                'categoria': categoria_resposta, # Inclui a categoria nas estatísticas
                'contagem': contagem
            })
        else:
            estatisticas.append({
                'id': id_resp,
                'titulo': f"Resposta ID {id_resp} (Excluída)",
                'categoria': "Desconhecida", # Categoria para respostas excluídas
                'contagem': contagem
            })

    estatisticas.sort(key=lambda x: x['contagem'], reverse=True)

    return jsonify(estatisticas=estatisticas)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
