from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import fitz  # PyMuPDF
import os
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Mude para uma chave mais segura em produção

# Configurações
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

# Criar pastas se não existirem
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extrair_texto_de_pdf(caminho_pdf):
    """
    Extrai o texto de um arquivo PDF e retorna como string.
    """
    try:
        documento = fitz.open(caminho_pdf)
        texto_completo = ""
        
        for pagina_num in range(len(documento)):
            pagina = documento.load_page(pagina_num)
            texto_completo += pagina.get_text()
            texto_completo += f"\n--- Fim da Página {pagina_num + 1} ---\n\n"
        
        documento.close()
        return texto_completo
    except Exception as e:
        raise Exception(f"Erro ao processar PDF: {str(e)}")

def gerar_prompt_resumo(texto, tipo_resumo):
    """
    Gera um prompt estruturado para o Gemini criar um resumo baseado no tipo selecionado.
    """
    prompts = {
        'estruturado': f"""Por favor, analise o seguinte texto extraído de um PDF e crie um RESUMO ESTRUTURADO seguindo este formato:

## RESUMO EXECUTIVO
[Resumo de 2-3 parágrafos dos pontos principais]

## TÓPICOS PRINCIPAIS
[Lista dos principais temas abordados]

## PONTOS-CHAVE
[Bullet points com as informações mais importantes]

## CONCLUSÕES
[Principais conclusões ou takeaways]

## PALAVRAS-CHAVE
[5-10 palavras-chave relevantes]

Este tipo de resumo serve para organizar a informação de forma lógica e escaneável, permitindo que o leitor encontre rapidamente os dados que procura. É ideal para quem precisa de uma visão geral detalhada e bem categorizada.

Texto para análise:

{texto[:8000]}{'...' if len(texto) > 8000 else ''}

Por favor, forneça um resumo estruturado e bem organizado.""",
        
        'indicativo': f"""Por favor, analise o seguinte texto extraído de um PDF e crie um RESUMO INDICATIVO.

O resumo indicativo deve:
- Simplesmente apontar o conteúdo do documento, sem entrar em detalhes
- Funcionar como uma etiqueta ou "teaser"
- Ajudar o leitor a decidir se precisa ou não ler o documento completo
- Ser curto e direto ao ponto (máximo 3-4 frases)

Este tipo de resumo é perfeito para catálogos, bases de dados ou para quem está apenas avaliando se o documento é relevante para sua área de estudo ou trabalho.

Texto para análise:

{texto[:8000]}{'...' if len(texto) > 8000 else ''}

Por favor, forneça um resumo indicativo conciso.""",
        
        'informativo': f"""Por favor, analise o seguinte texto extraído de um PDF e crie um RESUMO INFORMATIVO.

O resumo informativo deve:
- Apresentar as informações principais do texto original
- Funcionar como um substituto do documento original
- Permitir que quem lê absorva os pontos-chave sem precisar consultar a fonte
- Incluir fatos essenciais, dados importantes e conclusões principais
- Ser mais detalhado que um resumo indicativo, mas mais conciso que o texto original

Este tipo de resumo é útil para quem precisa dos fatos essenciais de forma rápida e condensada.

Texto para análise:

{texto[:8000]}{'...' if len(texto) > 8000 else ''}

Por favor, forneça um resumo informativo completo.""",
        
        'critico': f"""Por favor, analise o seguinte texto extraído de um PDF e crie um RESUMO CRÍTICO (ou ANALÍTICO).

O resumo crítico deve:
- Ir além da descrição e incluir uma análise ou avaliação sobre o material
- Não apenas dizer o que o texto contém, mas também comentar sobre sua relevância, qualidade ou limitações
- Adicionar uma camada de contexto e análise crítica
- Avaliar a credibilidade, atualidade e aplicabilidade do conteúdo
- Incluir recomendações sobre o uso ou valor do material

Este tipo de resumo é útil para quem precisa tomar uma decisão baseada no valor do documento.

Texto para análise:

{texto[:8000]}{'...' if len(texto) > 8000 else ''}

Por favor, forneça um resumo crítico com análise e avaliação do conteúdo."""
    }
    
    return prompts.get(tipo_resumo, prompts['estruturado'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            # Salvar arquivo com nome seguro
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            # Extrair texto
            texto_extraido = extrair_texto_de_pdf(filepath)
            
            # Salvar texto extraído
            nome_base = os.path.splitext(unique_filename)[0]
            txt_filename = f"{nome_base}_texto.txt"
            txt_filepath = os.path.join(OUTPUT_FOLDER, txt_filename)
            
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(texto_extraido)
            
            # Limpar arquivo PDF temporário
            os.remove(filepath)
            
            # Limpar e preparar texto para JSON
            texto_limpo = texto_extraido.replace('\r\n', '\n').replace('\r', '\n')
            # Remover caracteres de controle que podem causar problemas
            import re
            texto_limpo = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto_limpo)
            
            flash(f'Texto extraído com sucesso! Arquivo: {txt_filename}')
            return render_template('resultado.html', 
                                 filename=txt_filename, 
                                 texto=texto_limpo[:1000] + '...' if len(texto_limpo) > 1000 else texto_limpo,
                                 texto_completo=texto_limpo)
            
        except Exception as e:
            flash(f'Erro ao processar arquivo: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Tipo de arquivo não permitido. Apenas arquivos PDF são aceitos.')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        flash(f'Erro ao baixar arquivo: {str(e)}')
        return redirect(url_for('index'))

@app.route('/gerar-resumo', methods=['POST'])
def gerar_resumo():
    try:
        data = request.get_json()
        texto = data.get('texto', '')
        tipo_resumo = data.get('tipo_resumo', 'estruturado')
        
        # Gerar prompt baseado no tipo selecionado
        prompt = gerar_prompt_resumo(texto, tipo_resumo)
        
        # Salvar prompt em arquivo para facilitar o copy/paste
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"prompt_gemini_{tipo_resumo}_{timestamp}.txt"
        prompt_filepath = os.path.join(OUTPUT_FOLDER, prompt_filename)
        
        with open(prompt_filepath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return jsonify({
            'success': True, 
            'message': f'Prompt para resumo {tipo_resumo} salvo com sucesso!',
            'prompt': prompt,
            'prompt_file': prompt_filename,
            'gemini_url': 'https://gemini.google.com/app'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)