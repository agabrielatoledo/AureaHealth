import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

app = Flask(__name__)

# configurações RAG
PASTA_PDFS = "database"   
PASTA_MODELO = "model"    
NOME_MODELO = "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf" 
PASTA_DB_IA = "chroma_db" 

ia_chain = None

def iniciar_ia():
    global ia_chain
    print("\nIniciando sistema RAG")
    
    caminho_modelo_completo = os.path.join(PASTA_MODELO, NOME_MODELO)
    
    if not os.path.exists(caminho_modelo_completo):
        print(f"❌ ERRO: Modelo não encontrado em {caminho_modelo_completo}")
        return

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(PASTA_DB_IA) and os.listdir(PASTA_DB_IA):
        print("✅ Banco de dados encontrado. Carregando...")
        db = Chroma(persist_directory=PASTA_DB_IA, embedding_function=embeddings)
    else:
        print("⚠️ Criando banco de dados a partir dos PDFs...")
        if not os.path.exists(PASTA_PDFS):
            os.makedirs(PASTA_PDFS)
        
        loader = DirectoryLoader(PASTA_PDFS, glob="./*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        
        if not documents:
            print("❌ NENHUM PDF ENCONTRADO.")
            db = None 
        else:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            db = Chroma.from_documents(chunks, embeddings, persist_directory=PASTA_DB_IA)
            db.persist()
            print(f"✅ Processados {len(chunks)} trechos.")

    print(f"🦙 Carregando Llama 3...")
    llm = LlamaCpp(
        model_path=caminho_modelo_completo,
        temperature=0.1,  
        max_tokens=512,
        n_ctx=4096,
        n_gpu_layers=-1,
        verbose=False,
        stop=["<|eot_id|>"] 
    )

    if db:
        retriever = db.as_retriever(search_kwargs={"k": 3})
        template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Você é um assistente médico especialista em cirurgia cardíaca.
Responda à pergunta do usuário usando APENAS o contexto fornecido abaixo.
Se a resposta não estiver no contexto, diga que não sabe.
Contexto:
{context}<|eot_id|><|start_header_id|>user<|end_header_id|>
Pergunta: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        
        ia_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt}
        )
    else:
        ia_chain = llm 

    print("✅ SISTEMA PRONTO")

### banco de dados e CRUD
def init_sql_db():
    conn = sqlite3.connect('pacientes.db')
    cursor = conn.cursor()
    
    # table diário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            paciente TEXT NOT NULL, 
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # table usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL
        )
    ''')

    # usuários FIXOS 
    usuarios_padrao = [
        ('joao@cardio.com', '1234', 'João da Silva Rosa'),
        ('maria@cardio.com', '1234', 'Maria Oliveira Santos')
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO usuarios VALUES (?,?,?)', usuarios_padrao)
    
    conn.commit()
    conn.close()

## fluxos da aplicação
@app.route('/')
def home():
    return render_template('index.html')

# fluxo de login
@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email')
    senha = dados.get('senha')
    
    conn = sqlite3.connect('pacientes.db')
    cursor = conn.cursor()
    
    # valida login no banco
    cursor.execute("SELECT nome FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        return jsonify({'status': 'ok', 'nome': usuario[0]})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'E-mail ou senha incorretos!'}), 401

@app.route('/api/chat', methods=['POST'])
def chat():
    if not ia_chain: return jsonify({'resposta': "Erro: IA carregando..."})
    dados = request.json
    pergunta = dados.get('msg')
    try:
        if hasattr(ia_chain, 'invoke'):
            resultado = ia_chain.invoke({"query": pergunta, "question": pergunta})
            return jsonify({'resposta': resultado['result']})
        else:
            return jsonify({'resposta': str(ia_chain(pergunta))})
    except Exception as e:
        print(f"ERRO IA: {e}")
        return jsonify({'resposta': f"⚠️ ERRO TÉCNICO: {str(e)}"})

@app.route('/api/diario', methods=['GET', 'POST'])
def gerenciar_diario():
    conn = sqlite3.connect('pacientes.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        texto = request.json.get('texto')
        paciente = request.json.get('paciente')
        cursor.execute("INSERT INTO diario (texto, paciente) VALUES (?, ?)", (texto, paciente))
        conn.commit()
        conn.close()
        return jsonify({'status': 'salvo'})
    
    paciente_atual = request.args.get('paciente')
    cursor.execute("SELECT * FROM diario WHERE paciente = ? ORDER BY id DESC", (paciente_atual,))
    notas = cursor.fetchall()
    conn.close()
    return jsonify(notas)

@app.route('/api/diario/<int:id>', methods=['PUT'])
def atualizar_nota(id):
    conn = sqlite3.connect('pacientes.db')
    cursor = conn.cursor()
    texto_novo = request.json.get('texto')
    cursor.execute("UPDATE diario SET texto = ? WHERE id = ?", (texto_novo, id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'atualizado'})

@app.route('/api/diario/<int:id>', methods=['DELETE'])
def deletar_nota(id):
    conn = sqlite3.connect('pacientes.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diario WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deletado'})

@app.route('/api/clima')
def obter_clima():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-30.03&longitude=-51.23&current=temperature_2m"
        resp = requests.get(url, timeout=2)
        dados = resp.json()
        temp = dados['current']['temperature_2m']
        
        if temp > 30:
            aviso = "⚠️ Calor excessivo! Beba muita água e evite o sol direto para não baixar a pressão."
        elif temp > 25:
            aviso = "☀️ Dia quente. Mantenha-se hidratado e use roupas leves."
        elif temp < 15:
            aviso = "❄️ Frio alerta! O ar gelado exige mais do coração. Agasalhe-se bem ao sair."
        elif temp < 10:
            aviso = "🥶 Frio intenso! Se possível, fique em casa e mantenha as extremidades aquecidas."
        else:
            aviso = "✅ Clima agradável! Ótimo momento para caminhadas leves (se liberadas)."

        return jsonify({"info": f"🌡️ Porto Alegre: {temp}°C. {aviso}"})
        
    except Exception as e:
        print(f"Erro Clima: {e}")
        return jsonify({"info": "🌡️ Verifique a temperatura antes de sair de casa."})

if __name__ == '__main__':
    init_sql_db()
    iniciar_ia()
    print("\n🔗 http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)