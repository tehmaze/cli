class History(list):
    def __init__(self, *args):
        super(History, self).__init__(*args)
        position = -1

    def reset(self):
        self.position = len(self)

    def backward(self):
        self.position = max(0, self.position - 1)
        return self[self.position]

    def forward(self):
        self.position = min(len(self) - 1, self.position + 1)
        return self[self.position]

    def complete_backward(self, item):
        for line in iter(reversed(self)):
            if item in line:
                return line

    def complete_forward(self, item):
        for line in iter(self):
            if item in line:
                return line

class HistoryFile(History):
    def __init__(self, filename, mode='a'):
        self.filename = filename
        self.load()
        self.handle = open(filename, mode)

    def load(self):
        for line in file(self.filename):
            super(History, self).append(line.strip())

    def append(self, line):
        super(History, self).append(line)
        self.handle.write(''.join([line, '\n']))
        self.handle.flush()

