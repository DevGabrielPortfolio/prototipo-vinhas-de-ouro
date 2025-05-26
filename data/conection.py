import mysql.connector
from mysql.connector import Error

class Conection:
    # Ajuste aqui as suas credenciais do banco de dados
    _HOST = 'localhost'
    _DATABASE = 'db_vinhas_de_ouro' # Substitua pelo nome da sua base de dados
    _USER = 'root'           # Substitua pelo seu usuário do MySQL
    _PASSWORD = 'root'         # Substitua pela sua senha do MySQL

    @staticmethod
    def create_conection():
        try:
            conn = mysql.connector.connect(
                host=Conection._HOST,
                database=Conection._DATABASE,
                user=Conection._USER,
                password=Conection._PASSWORD
            )
            if conn.is_connected():
                # print("Conexão bem-sucedida ao banco de dados!")
                return conn
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            return None # Retorna None em caso de falha na conexão
        return None # Retorna None se não conectar