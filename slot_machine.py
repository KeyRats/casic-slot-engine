import random
import json
from itertools import groupby


class SlotMachine:
    def __init__(self, config_path):
        self.config = self.read_config(config_path)
        #  creating a character matrix of the desired size
        self.matrix = [
            ["x"] * self.config["scale"][0] for i in range(self.config["scale"][1])
        ]
        #  calculation of the probability of a symbol falling out with a rarity of 1
        probability_coef = self.symbol_probability()
        #  getting a list of symbols and their parameters
        symbols_list = self.symbol_list(probability_coef)

        #  creating a list of slot symbols of class SlotMachine.Symbol
        self.symbols = list()
        for symbol in symbols_list:
            self.symbols.append(
                self.Symbol(
                    symbol["tag"],
                    symbol["multiplier"],
                    symbol["probability"],
                    symbol["range"],
                )
            )

        for symbol in self.symbols:
            symbol.print()
        #  getting a list of slot lines based on a template from the config minus lines that do not fit into the slot
        lines_ = self.lines_list()

        #  creating a list of slot lines
        self.lines = list()
        for line in lines_:
            symbols_ = list()
            for pos in line:
                symbols_.append(self.Placed_Symbol(pos))
            self.lines.append(symbols_)

        #  creating a list of multiplier coefficients by lines
        self.lines_multiplier = self.config["lines_multiplier"]
        #  extracting from the config the minimum number of replays by lines
        self.min_line = self.config["min_line"]
        #  creating a list of winning lines
        self.win_lines = list()

    def calculate_probability_and_RTP(self):
        def get_all_combinations(
            n, i=1, sequence=[]
        ):  #  n - number of positions, other arguments needed
            #  for recursion
            print(i)
            print(len(sequence))
            if i > n:
                return sequence
            else:
                new_sequence = list()
                if len(sequence) == 0:
                    for symbol in self.symbols:
                        new_sequence.append([symbol])
                    return get_all_combinations(n, i + 1, new_sequence)
                else:
                    for symbol in self.symbols:
                        for pos in sequence:
                            comb = list()
                            comb.append(symbol)
                            for sym in pos:
                                comb.append(sym)
                            new_sequence.append(comb)
                    return get_all_combinations(n, i + 1, new_sequence)

        #  turning a list of slot lines into a one-dimensional array of positions
        win_positions = list()
        for line in self.lines:
            line_ = list()
            for sym in line:
                line_.append(
                    self.Placed_Symbol(
                        sym.indexes[0] * self.config["scale"][0] + sym.indexes[1]
                    )
                )
            win_positions.append(line_)

        RTP = 0
        total_prob = 0
        for comb in get_all_combinations(
            self.config["scale"][1] * self.config["scale"][0]
        ):
            self.fill_lines_with_symbols(comb, win_positions, "1d")
            self.pick_wining_lines(win_positions)
            prob = 0
            total_win = 0
            for line in self.win_lines:
                win_symbol = self.Symbol()
                for symbol in line:
                    win_symbol = symbol
                    if symbol.tag != " wild":
                        break
                total_win = (
                    total_win
                    + win_symbol.multiplier * self.lines_multiplier[str(len(line))]
                )
            if len(self.win_lines) != 0:
                prob = 1
                for pos_ in comb:
                    prob = prob * pos_.probability
            total_prob = total_prob + prob
            RTP = RTP + total_win * prob
        print("Theoretical chance to win(alt_place): " + str(total_prob))
        print("Theoretical RTP(alt_place): " + str(RTP))

    def __str__(self):
        matrix = str()
        for string in self.matrix:
            for cell in string:
                matrix += "| " + str(cell) + " "
            matrix += "|\n"
        return matrix

    def print(self, matrix):
        out = ""
        for string in matrix:
            for cell in string:
                out += "| " + str(cell) + " "
            out += "|\n"
        print(out)

    def create_tag_matrix(self):
        """creates a matrix filled with character tags to output to json"""
        tag_matrix = [
            ["x"] * self.config["scale"][0] for i in range(self.config["scale"][1])
        ]
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[0])):
                tag_matrix[i][j] = str(self.matrix[i][j])
        return tag_matrix

    def print_win_matrix(self):
        """prints a matrix to the console, where the performances are highlighted with caps"""
        tag_matrix = self.create_tag_matrix()
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[0])):
                tag_matrix[i][j] = str(self.matrix[i][j])
        for line in self.win_lines:
            for symbol in line:
                tag_matrix[symbol.indexes[0]][symbol.indexes[1]] = tag_matrix[
                    symbol.indexes[0]
                ][symbol.indexes[1]].upper()
        matrix = ""
        for string in tag_matrix:
            for cell in string:
                matrix += "| " + str(cell) + " "
            matrix += "|\n"
        print(matrix)

    def symbol_probability(self):
        """calculates the probability of an event with a rarity of 1"""
        summ = 0
        for symbol in self.config["symbols"]:
            summ += 1 / symbol["rarity"]
        return 1 / summ

    def symbol_list(self, coef):
        """creates a list of dictionaries with information about symbols (name, multiplier, probability of falling out, segment boundaries for random)"""
        summ = 0
        symbols_ = list()
        for symbol in self.config["symbols"]:
            symbols_.append(
                {
                    "tag": symbol["tag"],
                    "multiplier": symbol["multiplier"],
                    "probability": coef / symbol["rarity"],
                    "range": summ,
                }
            )
            summ += coef / symbol["rarity"]
        return symbols_

    def lines_list(self):
        """creates sets of indices corresponding to line types, removes unnecessary ones, returns as a list"""
        line_list = list()
        for lin in self.config["lines"]:
            for i in range(len(self.matrix)):
                line = list()
                line.append([i, 0])
                k = 1
                l = i
                for dir in lin:
                    if dir == "s":
                        l = l
                    elif dir == "d":
                        l = l + 1
                    elif dir == "u":
                        l = l - 1
                    line.append([l, k])
                    k = k + 1
                line_list.append(line)
        blacklist = list()

        #  removal of lines that crawl out of the slot
        def remove_line(line):
            for pos in line:
                if (pos[0] < 0) or (pos[0] > self.config["scale"][1] - 1):
                    return False
            return True

        return list(filter(remove_line, line_list))

    def read_config(self, config_path):
        with open(config_path) as conf:
            return json.load(conf)

    def generate_symbols(self):
        """in each of the cells of the slot matrix, we generate symbols according to their probabilities, returns the matrix of the slot instance"""
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[0])):
                throw = random.uniform(0, 1)
                for k in range(len(self.symbols) - 1):
                    if (throw >= self.symbols[k].range) and (
                        throw <= self.symbols[k + 1].range
                    ):
                        self.matrix[i][j] = self.symbols[k]
                        break
                if throw >= self.symbols[len(self.symbols) - 1].range:
                    self.matrix[i][j] = self.symbols[len(self.symbols) - 1]
        return self.matrix

    def fill_lines_with_symbols(self, matrix=None, lines=None, type="2d"):
        """populates a list of slot lines with characters based on a character matrix"""
        if matrix is None:
            matrix = self.matrix
        if lines is None:
            lines = self.lines
        for line in lines:
            for symbol in line:
                if type == "2d":
                    symbol.get_symbol(matrix[symbol.indexes[0]][symbol.indexes[1]])
                if type == "1d":
                    symbol.get_symbol(matrix[symbol.indexes])
        return lines

    def pick_wining_lines(self, lines=None):
        """chooses winning lines from the list of slots and removes unnecessary repetitions, shortens them,
        if necessary, creates a list of winning lines filled with symbols (class Placed_Symbol)"""
        self.win_lines = list()
        if lines == None:
            lines = self.lines
        win_lines = list()
        for line in lines:
            line_ = list()
            line_.append(line[0])
            for i in range(1, len(line)):
                check = False
                if line[i - 1].tag == " wild":
                    if line[i].tag == " wild":
                        check = True
                    else:
                        check = True
                        k = 0
                        while k < i:
                            if (line[k].tag != line[i].tag) and (
                                line[k].tag != " wild"
                            ):
                                check = False
                                break
                            k = k + 1
                else:
                    if (line[i].tag == line[i - 1].tag) or (line[i].tag == " wild"):
                        check = True
                if check:
                    line_.append(line[i])
                else:
                    break
            if len(line_) >= self.min_line:
                win_lines.append(line_)

        #  removing unnecessary lines (repetitions, nesting)
        def remove_line(line):
            if win_lines.count(line) > 1:
                return False
            for line_ in win_lines:
                if line != line_:
                    if len(line) <= len(line_):
                        if line == line_[: len(line)]:
                            return False
            return True

        self.win_lines = list(filter(remove_line, win_lines))
        return self.win_lines

    def output_json(self):
        """based on the system matrix and the set of winning lines, generates a JSON string for displaying information"""
        win_lines_out = list()
        for line in self.win_lines:
            symbol_info_ = list()
            indexes_ = list()
            for symbol in line:
                if symbol.tag == " wild":
                    symbol_info_ = [symbol.tag, symbol.multiplier]
                else:
                    symbol_info_ = [symbol.tag, symbol.multiplier]
                    break
            for symbol in line:
                indexes_.append([symbol.indexes[0], symbol.indexes[1]])
            win_lines_out.append(
                {
                    "indexes": indexes_,
                    "symbol": symbol_info_[0],
                    "multiplier": symbol_info_[1]
                    * self.lines_multiplier[str(len(line))],
                }
            )

        roll_output = {"matrix": self.create_tag_matrix(), "win_lines": win_lines_out}
        return json.dumps(roll_output)

    def roll(self, debug=True):
        self.generate_symbols()
        self.fill_lines_with_symbols()
        self.pick_wining_lines()
        if debug:
            self.print_win_matrix()

        output = self.output_json()
        if debug:
            for win_line in json.loads(output)["win_lines"]:
                print(win_line)

        return output

    class Symbol:
        def __init__(self, tag="x", multiplier=1, probability=1, _range=1):
            self.tag = tag
            self.multiplier = multiplier
            self.probability = probability
            self.range = _range

        def print(self):
            print(f"{self.tag}, {self.probability}, {self.range}")

        def __str__(self):
            return str(self.tag)

    class Placed_Symbol(Symbol):
        def __init__(self, indexes, tag="x", multiplier=1, probability=1, _range=1):
            super().__init__(tag, multiplier, probability, _range)
            self.indexes = indexes

        def get_symbol(self, symbol):
            self.tag = symbol.tag
            self.multiplier = symbol.multiplier
            self.probability = symbol.probability
            self.range = symbol.range

        def __str__(self):
            return str(self.indexes) + ", " + str(self.tag)

        def __eq__(self, other):
            return (
                other is not None
                and self.tag == other.tag
                and self.indexes == other.indexes
            )
