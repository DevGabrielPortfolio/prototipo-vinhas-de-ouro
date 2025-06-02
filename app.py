from flask import Flask, render_template, redirect, request, flash, url_for, get_flashed_messages, session

from models.control_categories import Categories
from models.control_shopping_cart import ControlShoppingCart
from models.control_users import Users
from models.control_wines import Wines
from models.control_comentario import Comments


from functools import wraps

app = Flask(__name__)

app.secret_key = 'sua_chave_secreta_super_segura_aqui_12345'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'info')
            return redirect(url_for('login'))  # Redireciona para a rota de login
        return f(*args, **kwargs)

    return decorated_function


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)

    return redirect(url_for('main_page'))


@app.route('/')
def main_page():
    categorias = Categories.get_all_categories()

    category_id = request.args.get('categoria', type=int)

    vinhos = []
    if category_id:
        vinhos = Wines.get_wines_by_category(category_id)
        if not vinhos:
            flash(f'Nenhum vinho encontrado para a categoria selecionada.', 'info')
    else:
        vinhos = Wines.get_all_wines()
        if not vinhos:
            flash('Nenhum vinho cadastrado no momento.', 'info')

    return render_template('index.html', categorias=categorias, produtos=vinhos)

@app.route('/configuracoes-conta')
def create_acount():
    return render_template('create_acount.html')


@app.route('/cadastrar_usuario', methods=['POST'])
def register_user():
    username = request.form['username']
    email = request.form['email']
    telefone = request.form['telefone']

    cep = request.form['cep']
    rua = request.form['rua']
    numero = request.form['numero']
    bairro = request.form['bairro']
    cidade = request.form['cidade']
    estado = request.form['uf']

    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        flash('As senhas não coincidem!', 'danger')
        return redirect(url_for('create_acount'))

    if len(password) < 6:
        flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
        return redirect(url_for('create_acount'))

    try:
        user_id = Users.register_user(
            username=username,
            password_plaintext=password,  # Passando a senha em texto puro aqui!
            telefone=telefone,
            email=email,
            cep=cep,
            rua=rua,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado
        )

        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            flash('Cadastro realizado com sucesso. Bem-vindo(a)!', 'success')
            return redirect(url_for('main_page'))
        else:
            flash('Erro ao cadastrar usuário. O nome de usuário ou e-mail pode já estar em uso.', 'danger')
            return redirect(url_for('create_acount'))

    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {str(e)}. Tente novamente.', 'danger')
        return redirect(url_for('create_acount'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['username_or_email']
        password = request.form['password']

        user_id = Users.verify_user_credentials(login_input, password)

        if user_id:
            login_info = Users.verify_user_credentials(login_input, password)
            if login_info:
                user_id, username_from_db = login_info
                session['user_id'] = user_id
                session['username'] = username_from_db
                return redirect(url_for('main_page'))
            else:
                flash('Credenciais inválidas. Verifique seu usuário/e-mail e senha.', 'danger')
                return redirect(url_for('login'))
    else:
        flashed_messages = get_flashed_messages(with_categories=True)
        return render_template('login_page.html', flashed_messages=flashed_messages)


@app.route('/carrinho')
@login_required
def carrinho():
    id_usuario = session['user_id']
    if not id_usuario:
        flash('Você precisa estar logado para ver seu carrinho.', 'danger')
        return redirect(url_for('login'))

    itens_carrinho = ControlShoppingCart.get_itens_carrinho_por_usuario(id_usuario)
    total_carrinho = sum(item['preco_unitario'] * item['quantidade'] for item in itens_carrinho)
    return render_template('shopping_cart.html', itens_carrinho=itens_carrinho, total_carrinho=total_carrinho)

@app.route('/vinho/<int:vinho_id>')
def detalhes_vinho(vinho_id):
    print(f"DEBUG: Tentando buscar detalhes para o vinho_id = {vinho_id}")
    vinho = Wines.get_wine_by_id(vinho_id)
    if vinho:
        categorias = Categories.get_all_categories() # Ou apenas Categories se for uma classe estática

        # CHAME A FUNÇÃO PARA BUSCAR OS COMENTÁRIOS AQUI
        comentarios = Comments.get_comments_by_product_id(vinho_id)

        # PASSE OS COMENTÁRIOS PARA O TEMPLATE
        return render_template('detalhes_vinho.html', 
                               vinho=vinho, 
                               categorias=categorias, 
                               comentarios=comentarios, # <--- ESSENCIAL
                               id_produto=vinho_id) # Garante que o ID do produto está disponível para o formulário de comentário
    else:
        flash('Vinho não encontrado.', 'danger')
        return redirect(url_for('main_page'))


# ...
@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    print(f"DEBUG_APP: Requisição POST recebida em /adicionar_ao_carrinho.")
    print(f"DEBUG_APP: Dados do formulário: {request.form}") # ESTA É MUITO IMPORTANTE!

    id_usuario = session.get('user_id') # Ou 1 para teste
    print(f"DEBUG_APP: ID do usuário (da sessão): {id_usuario}")

    produto_id = request.form.get('produto_id', type=int) # OU 'vinho_id' se o HTML ainda usa
    quantidade = request.form.get('quantidade', type=int)
    print(f"DEBUG_APP: Produto ID lido: {produto_id}, Quantidade lida: {quantidade}") # IMPORTANTE!

    if produto_id is None or quantidade is None or quantidade <= 0:
        print(f"DEBUG_APP: Validação falhou: produto_id={produto_id}, quantidade={quantidade}")
        flash('Dados inválidos para adicionar ao carrinho.', 'danger')
        # ...
        return redirect(url_for('main_page')) # Ou detalhes_vinho

    sucesso = ControlShoppingCart.adicionar_ou_atualizar_item(id_usuario, produto_id, quantidade)
    print(f"DEBUG_APP: Retorno de ControlShoppingCart: {sucesso}") # CRÍTICO!

    if sucesso:
        flash('Produto adicionado/atualizado no carrinho com sucesso!', 'success')
    else:
        flash('Ocorreu um erro ao adicionar o produto ao carrinho.', 'danger')

    return redirect(url_for('carrinho'))


@app.route('/remover_do_carrinho', methods=['POST'])
def remover_do_carrinho():
    id_usuario = session.get('user_id')

    if not id_usuario:
        flash('Você precisa estar logado para remover itens do carrinho.', 'danger')
        return redirect(url_for('login'))

    # Pega o ID do produto do formulário (agora o 'name' no HTML é 'produto_id')
    produto_id = request.form.get('produto_id', type=int)

    if produto_id is None:
        flash('ID do produto inválido para remoção.', 'danger')
        return redirect(url_for('carrinho'))

    sucesso = ControlShoppingCart.remover_item_carrinho(id_usuario, produto_id)

    if sucesso:
        flash('Produto removido do carrinho com sucesso!', 'success')
    else:
        flash('Ocorreu um erro ao remover o produto do carrinho.', 'danger')

    return redirect(url_for('carrinho')) # Redireciona de volta para a página do carrinho

@app.route('/atualizar_quantidade_carrinho', methods=['POST'])
def atualizar_quantidade_carrinho():
    id_usuario = session.get('user_id')

    if not id_usuario:
        flash('Você precisa estar logado para atualizar o carrinho.', 'danger')
        return redirect(url_for('login'))

    produto_id = request.form.get('produto_id', type=int)
    nova_quantidade = request.form.get('quantidade', type=int) # Novo nome do campo

    if produto_id is None or nova_quantidade is None or nova_quantidade < 1:
        flash('Dados inválidos para atualizar a quantidade do carrinho.', 'danger')
        return redirect(url_for('carrinho'))

    # Se a nova quantidade for 0, podemos remover o item (opcional, mas boa prática)
    if nova_quantidade == 0:
        sucesso = ControlShoppingCart.remover_item_carrinho(id_usuario, produto_id)
        if sucesso:
            flash('Produto removido do carrinho.', 'info')
        else:
            flash('Erro ao remover produto do carrinho.', 'danger')
    else:
        sucesso = ControlShoppingCart.atualizar_quantidade_item(id_usuario, produto_id, nova_quantidade)
        if sucesso:
            flash('Quantidade do produto atualizada!', 'success')
        else:
            flash('Ocorreu um erro ao atualizar a quantidade do produto.', 'danger')

    return redirect(url_for('carrinho'))


@app.route('/post/cadastrarmensagem', methods=['POST'])
@login_required  # só permite quem está logado comentar
def cadastrar_comentario():
    id_usuario = session.get('user_id')
    id_produto = request.form.get('id_produto', type=int)
    comentario_texto = request.form.get('comentario', '').strip()

    if not comentario_texto:
        flash('O comentário não pode ser vazio.', 'warning')
        return redirect(url_for('detalhes_vinho', vinho_id=id_produto))

    sucesso = Comments.add_comment(id_usuario, id_produto, comentario_texto)

    if sucesso:
        flash('Comentário enviado com sucesso!', 'success')
    else:
        flash('Erro ao enviar o comentário. Tente novamente.', 'danger')

    return redirect(url_for('detalhes_vinho', vinho_id=id_produto))



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)