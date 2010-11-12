import shlex

class Token(str):
    pass

class TokenPipe(Token):
    pass

class TokenRedirect(Token):
    pass

class TokenWord(Token):
    pass

def parse(line, posix=True):
    lexer = shlex.shlex(line, posix=posix)
    lexer.wordchars += ',./[]{}~!@$%^&*()-_=+:;'

    while True:
        token = lexer.get_token()
        if not token:
            break

        if token == '|':
            yield TokenPipe(token)

        elif token in ['<', '>']:
            yield TokenRedirect(token)

        else:
            yield TokenWord(token)

if __name__ == '__main__':
    line = 'this "is a" \'<\' |test \'with "pipes\' > redirect'

    for token in parse(line):
        print token.__class__.__name__, token

