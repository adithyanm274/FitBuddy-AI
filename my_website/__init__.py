import pymysql
pymysql.version_info = (2, 2, 1, 'final', 0)  # or whatever version you want to fake
pymysql.install_as_MySQLdb()