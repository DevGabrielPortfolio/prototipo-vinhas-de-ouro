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
    """
    Decorador para garantir que o usuário esteja logado para acessar certas rotas.
    Redireciona para a página de login se o user_id não estiver na sessão.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'info')
            return redirect(url_for('login'))  # Redireciona para a rota de login
        return f(*args, **kwargs)

    return decorated_function


@app.route('/logout')
def logout():
    """
    Rota para deslogar o usuário.
    Remove o user_id e username da sessão e redireciona para a página principal.
    """
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado com sucesso.', 'success') # Adiciona uma mensagem de sucesso ao deslogar
    return redirect(url_for('main_page'))


@app.route('/')
def main_page():
    """
    Rota da página principal que exibe categorias e vinhos.
    Permite filtrar vinhos por categoria.
    """
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
    """
    Rota para a página de criação de conta/configurações.
    """
    return render_template('create_acount.html')


@app.route('/cadastrar_usuario', methods=['POST'])
def register_user():
    """
    Rota para processar o cadastro de um novo usuário.
    Valida senhas e dados de endereço antes de registrar.
    """
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
    """
    Rota para a página de login e processamento do login.
    Verifica as credenciais do usuário.
    """
    if request.method == 'POST':
        login_input = request.form['username_or_email']
        password = request.form['password']

        login_info = Users.verify_user_credentials(login_input, password)

        if login_info:
            user_id, username_from_db = login_info
            session['user_id'] = user_id
            session['username'] = username_from_db
            flash(f'Bem-vindo(a) de volta, {username_from_db}!', 'success') # Mensagem de sucesso no login
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
    """
    Rota para exibir o carrinho de compras do usuário logado.
    """
    id_usuario = session['user_id']
    # A verificação de id_usuario já é feita pelo decorador login_required
    # if not id_usuario:
    #     flash('Você precisa estar logado para ver seu carrinho.', 'danger')
    #     return redirect(url_for('login'))

    itens_carrinho = ControlShoppingCart.get_itens_carrinho_por_usuario(id_usuario)
    total_carrinho = sum(item['preco_unitario'] * item['quantidade'] for item in itens_carrinho)
    return render_template('shopping_cart.html', itens_carrinho=itens_carrinho, total_carrinho=total_carrinho)

@app.route('/vinho/<int:vinho_id>')
def detalhes_vinho(vinho_id):
    """
    Rota para exibir os detalhes de um vinho específico, incluindo comentários.
    """
    print(f"DEBUG: Tentando buscar detalhes para o vinho_id = {vinho_id}")
    vinho = Wines.get_wine_by_id(vinho_id)
    if vinho:
        categorias = Categories.get_all_categories()

        # CHAME A FUNÇÃO PARA BUSCAR OS COMENTÁRIOS AQUI
        comentarios = Comments.get_comments_by_product_id(vinho_id)

        # PASSE OS COMENTÁRIOS PARA O TEMPLATE
        return render_template('detalhes_vinho.html', 
                               vinho=vinho, 
                               categorias=categorias, 
                               comentarios=comentarios, 
                               id_produto=vinho_id) 
    else:
        flash('Vinho não encontrado.', 'danger')
        return redirect(url_for('main_page'))


@app.route('/adicionar_ao_carrinho', methods=['POST'])
@login_required # Garante que apenas usuários logados possam adicionar ao carrinho
def adicionar_ao_carrinho():
    """
    Rota para adicionar ou atualizar um item no carrinho de compras.
    """
    print(f"DEBUG_APP: Requisição POST recebida em /adicionar_ao_carrinho.")
    print(f"DEBUG_APP: Dados do formulário: {request.form}")

    id_usuario = session.get('user_id')
    print(f"DEBUG_APP: ID do usuário (da sessão): {id_usuario}")

    produto_id = request.form.get('produto_id', type=int)
    quantidade = request.form.get('quantidade', type=int)
    print(f"DEBUG_APP: Produto ID lido: {produto_id}, Quantidade lida: {quantidade}")

    if produto_id is None or quantidade is None or quantidade <= 0:
        print(f"DEBUG_APP: Validação falhou: produto_id={produto_id}, quantidade={quantidade}")
        flash('Dados inválidos para adicionar ao carrinho.', 'danger')
        return redirect(url_for('main_page')) # Redireciona para a página principal ou detalhes do vinho

    sucesso = ControlShoppingCart.adicionar_ou_atualizar_item(id_usuario, produto_id, quantidade)
    print(f"DEBUG_APP: Retorno de ControlShoppingCart: {sucesso}")

    if sucesso:
        flash('Produto adicionado/atualizado no carrinho com sucesso!', 'success')
    else:
        flash('Ocorreu um erro ao adicionar o produto ao carrinho.', 'danger')

    return redirect(url_for('carrinho'))


@app.route('/remover_do_carrinho', methods=['POST'])
@login_required # Garante que apenas usuários logados possam remover do carrinho
def remover_do_carrinho():
    """
    Rota para remover um item do carrinho de compras.
    """
    id_usuario = session.get('user_id')

    produto_id = request.form.get('produto_id', type=int)

    if produto_id is None:
        flash('ID do produto inválido para remoção.', 'danger')
        return redirect(url_for('carrinho'))

    sucesso = ControlShoppingCart.remover_item_carrinho(id_usuario, produto_id)

    if sucesso:
        flash('Produto removido do carrinho com sucesso!', 'success')
    else:
        flash('Ocorreu um erro ao remover o produto do carrinho.', 'danger')

    return redirect(url_for('carrinho'))


@app.route('/atualizar_quantidade_carrinho', methods=['POST'])
@login_required # Garante que apenas usuários logados possam atualizar o carrinho
def atualizar_quantidade_carrinho():
    """
    Rota para atualizar a quantidade de um item no carrinho.
    Se a quantidade for 0, o item é removido.
    """
    id_usuario = session.get('user_id')

    produto_id = request.form.get('produto_id', type=int)
    nova_quantidade = request.form.get('quantidade', type=int)

    if produto_id is None or nova_quantidade is None or nova_quantidade < 0: # Quantidade pode ser 0 para remover
        flash('Dados inválidos para atualizar a quantidade do carrinho.', 'danger')
        return redirect(url_for('carrinho'))

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
@login_required
def cadastrar_comentario():
    """
    Rota para cadastrar um novo comentário em um produto.
    """
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


@app.route('/finalizar_compra')
@login_required
def finalizar_compra():
    """
    Rota para a página de finalização de compra/pagamento.
    Obtém os itens reais do carrinho do usuário e o total.
    """
    id_usuario = session.get('user_id')
    # A verificação de id_usuario já é feita pelo decorador login_required
    # if not id_usuario:
    #     flash('Você precisa estar logado para finalizar a compra.', 'danger')
    #     return redirect(url_for('login'))

    # Obtém os itens do carrinho para calcular o total
    itens_carrinho = ControlShoppingCart.get_itens_carrinho_por_usuario(id_usuario)
    total_carrinho = sum(item['preco_unitario'] * item['quantidade'] for item in itens_carrinho)

    # Renderiza a página de simulação de pagamento, passando o total E os itens do carrinho
    return render_template('payment_simulation.html', itens_carrinho=itens_carrinho, total_carrinho=total_carrinho)

@app.route('/confirmacao_pedido')
@login_required # Garante que o usuário esteja logado para limpar o carrinho
def confirmacao_pedido():
    """
    Rota para exibir a página de confirmação após um pagamento simulado.
    Limpa o carrinho do usuário após a confirmação do pedido.
    """
    id_usuario = session.get('user_id')

    if id_usuario:
        # Chama o método para limpar o carrinho do usuário
        # É crucial que ControlShoppingCart.clear_cart(id_usuario) esteja implementado
        # na sua classe ControlShoppingCart para remover os itens do banco de dados.
        ControlShoppingCart.clear_cart(id_usuario)
        flash('Seu carrinho foi limpo com sucesso após a finalização do pedido.', 'success')
    else:
        # Esta condição não deve ser atingida devido ao @login_required, mas serve como salvaguarda.
        flash('Não foi possível limpar o carrinho. Usuário não identificado.', 'warning')

    return render_template('order_confirmation.html')



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

