// Rubik cube engine (C++17), improved version of the original MatriceDesfasurata program.
//
// Reads a script and writes the unfolded cube after every step, in the same text format the
// Python app exports (tests/test_cpp_parity.py keeps the two byte-identical).
//
//   g++ -std=c++17 -O2 -o rubik_engine rubik_engine.cpp
//   ./rubik_engine script.txt [MatriceDesfasurata.txt]      (without arguments: stdin -> stdout)
//
// Script: first line is the cube size (2..8); every next line is ONE step. Moves of a step are
// joined with '+'; a step counts as one however many moves/turns it contains. Layers are 1-based.
//
//   3
//   row 2 right x3 + col 3 up x2      <- one step
//   rows 1-2 left                      <- (also accepted: "row 1-2 left")
//   # lines starting with # are comments
//
// Fixes compared to the original: the "two adjacent rows" checks used || instead of &&, so they
// always refused; turning an outer layer now also rotates the face it touches; every move is
// validated before anything changes.
#include <algorithm>
#include <array>
#include <cctype>
#include <fstream>
#include <iostream>
#include <iterator>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr int kMinSize = 2;
constexpr int kMaxSize = 8;
constexpr int kMaxWidth = 2;
constexpr int kMaxTimes = 9;
constexpr int kFaceCount = 6;

// Face ids double as the initial sticker value (1..6) exactly like the original program.
enum Face { Up, Front, Right, Back, Left, Down };
constexpr std::array<Face, 4> kBand = {Front, Right, Back, Left};

enum class Direction { Right, Left, Up, Down };

struct Cell { int face, row, col; };
struct Transfer { Cell from, to; };
struct Move { Direction direction; int layer; int width; int times; };
using Step = std::vector<Move>;

bool movesRows(Direction d) { return d == Direction::Right || d == Direction::Left; }
bool isForward(Direction d) { return d == Direction::Right || d == Direction::Up; }

const char* directionName(Direction d) {
    switch (d) {
        case Direction::Right: return "right";
        case Direction::Left: return "left";
        case Direction::Up: return "up";
        default: return "down";
    }
}

// ---------- permutations ----------

std::vector<Transfer> rowRing(int size, int row) {  // right: Front -> Right -> Back -> Left -> Front
    std::vector<Transfer> transfers;
    for (int i = 0; i < 4; ++i)
        for (int col = 0; col < size; ++col)
            transfers.push_back({{kBand[i], row, col}, {kBand[(i + 1) % 4], row, col}});
    return transfers;
}

std::vector<Transfer> columnRing(int size, int col) {  // up: Front -> Up -> Back -> Down -> Front
    const int last = size - 1;
    std::vector<Transfer> transfers;
    for (int i = 0; i < size; ++i) {
        transfers.push_back({{Front, i, col}, {Up, i, col}});
        transfers.push_back({{Up, i, col}, {Back, last - i, last - col}});
        transfers.push_back({{Back, last - i, last - col}, {Down, i, col}});
        transfers.push_back({{Down, i, col}, {Front, i, col}});
    }
    return transfers;
}

std::vector<Transfer> faceRotation(int size, int face, bool clockwise) {
    const int last = size - 1;
    std::vector<Transfer> transfers;
    for (int a = 0; a < size; ++a)
        for (int b = 0; b < size; ++b)
            transfers.push_back({{face, a, b}, clockwise ? Cell{face, b, last - a} : Cell{face, last - b, a}});
    return transfers;
}

// The face that spins along with an outer layer, and whether it spins clockwise seen from outside.
std::optional<std::pair<int, bool>> outerFaceTurn(int size, Direction d, int layer) {
    if (movesRows(d)) {
        if (layer != 0 && layer != size - 1) return std::nullopt;
        const int face = layer == 0 ? Up : Down;
        return std::make_pair(face, (face == Down) == (d == Direction::Right));
    }
    if (layer != 0 && layer != size - 1) return std::nullopt;
    const int face = layer == 0 ? Left : Right;
    return std::make_pair(face, (face == Right) == (d == Direction::Up));
}

std::vector<Transfer> quarterTurnTransfers(int size, Direction d, int firstLayer, int width) {
    std::vector<Transfer> transfers;
    for (int layer = firstLayer; layer < firstLayer + width; ++layer) {
        std::vector<Transfer> ring = movesRows(d) ? rowRing(size, layer) : columnRing(size, layer);
        if (!isForward(d))
            for (Transfer& t : ring) std::swap(t.from, t.to);
        transfers.insert(transfers.end(), ring.begin(), ring.end());
        if (auto spin = outerFaceTurn(size, d, layer)) {
            std::vector<Transfer> rotation = faceRotation(size, spin->first, spin->second);
            transfers.insert(transfers.end(), rotation.begin(), rotation.end());
        }
    }
    return transfers;
}

// ---------- cube ----------

class Cube {
public:
    explicit Cube(int size) : size_(size) {
        for (int face = 0; face < kFaceCount; ++face)
            for (auto& row : faces_[face]) row.fill(face + 1);
    }

    void applyStep(const Step& step) {
        for (const Move& move : step) validate(move);  // validate first: a bad step changes nothing
        for (const Move& move : step)
            for (int turn = 0; turn < move.times; ++turn) quarterTurn(move);
    }

    int size() const { return size_; }
    int at(int face, int row, int col) const { return faces_[face][row][col]; }

private:
    using Matrix = std::array<std::array<int, kMaxSize>, kMaxSize>;

    void validate(const Move& move) const {
        if (move.width < 1 || move.width > kMaxWidth) throw std::runtime_error("width must be 1 or 2");
        if (move.times < 1 || move.times > kMaxTimes) throw std::runtime_error("times must be between 1 and 9");
        if (move.layer < 0 || move.layer + move.width > size_)
            throw std::runtime_error("layers are outside the cube");
    }

    void quarterTurn(const Move& move) {
        const auto before = faces_;
        for (const Transfer& t : quarterTurnTransfers(size_, move.direction, move.layer, move.width))
            faces_[t.to.face][t.to.row][t.to.col] = before[t.from.face][t.from.row][t.from.col];
    }

    int size_;
    std::array<Matrix, kFaceCount> faces_;
};

// ---------- text output (identical to cubix/export.py) ----------

std::vector<std::string> faceBlock(const Cube& cube, int face) {
    const int n = cube.size();
    std::string border;
    for (int i = 0; i < n + 2; ++i) border += i ? " *" : "*";
    std::vector<std::string> lines = {border};
    for (int row = 0; row < n; ++row) {
        std::string line = "* ";
        for (int col = 0; col < n; ++col) line += std::to_string(cube.at(face, row, col)) + " ";
        lines.push_back(line + "*");
    }
    lines.push_back(border);
    return lines;
}

std::string renderNet(const Cube& cube) {
    const int n = cube.size();
    const std::string indent(2 * n + 4, ' ');
    std::string out;
    for (const std::string& line : faceBlock(cube, Up)) out += indent + line + "\n";
    std::vector<std::vector<std::string>> band;
    for (Face face : kBand) band.push_back(faceBlock(cube, face));
    for (int line = 0; line < n + 2; ++line) {
        for (std::size_t i = 0; i < band.size(); ++i) out += (i ? " " : "") + band[i][line];
        out += "\n";
    }
    for (const std::string& line : faceBlock(cube, Down)) out += indent + line + "\n";
    return out;
}

std::string formatStep(const Step& step) {
    std::string text;
    for (const Move& move : step) {
        if (!text.empty()) text += " + ";
        const std::string layers = move.width == 1
            ? std::to_string(move.layer + 1)
            : std::to_string(move.layer + 1) + "-" + std::to_string(move.layer + move.width);
        text += std::string(movesRows(move.direction) ? "row " : "col ") + layers + " " +
                directionName(move.direction) + " x" + std::to_string(move.times);
    }
    return text;
}

// ---------- script parsing ----------

std::string lowercase(std::string text) {
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return std::tolower(c); });
    return text;
}

int parseNumber(const std::string& text, const std::string& context) {
    if (text.empty() || !std::all_of(text.begin(), text.end(), [](unsigned char c) { return std::isdigit(c); }))
        throw std::runtime_error("cannot read number '" + text + "' in: " + context);
    return std::stoi(text);
}

Move parseMove(const std::string& text) {
    std::istringstream words(lowercase(text));
    std::vector<std::string> w{std::istream_iterator<std::string>(words), std::istream_iterator<std::string>()};
    if (w.size() < 3 || w.size() > 4 || (w[0] != "row" && w[0] != "col"))
        throw std::runtime_error("cannot read move: " + text);

    Direction direction;
    if (w[2] == "right") direction = Direction::Right;
    else if (w[2] == "left") direction = Direction::Left;
    else if (w[2] == "up") direction = Direction::Up;
    else if (w[2] == "down") direction = Direction::Down;
    else throw std::runtime_error("unknown direction in: " + text);
    if (movesRows(direction) != (w[0] == "row"))
        throw std::runtime_error("a " + w[0] + " cannot move " + w[2] + ": " + text);

    const std::size_t dash = w[1].find('-');
    const int first = parseNumber(w[1].substr(0, dash), text);
    const int width = dash == std::string::npos ? 1 : parseNumber(w[1].substr(dash + 1), text) - first + 1;
    int times = 1;
    if (w.size() == 4) {
        if (w[3][0] != 'x') throw std::runtime_error("expected xN in: " + text);
        times = parseNumber(w[3].substr(1), text);
    }
    return {direction, first - 1, width, times};
}

Step parseStep(const std::string& line) {
    Step step;
    std::istringstream parts(line);
    std::string part;
    while (std::getline(parts, part, '+')) step.push_back(parseMove(part));
    return step;
}

bool isBlankOrComment(const std::string& line) {
    const std::size_t first = line.find_first_not_of(" \t\r");
    return first == std::string::npos || line[first] == '#';
}

void run(std::istream& script, std::ostream& out) {
    std::string line;
    std::optional<Cube> cube;
    int stepNumber = 0;
    while (std::getline(script, line)) {
        if (isBlankOrComment(line)) continue;
        if (!cube) {
            const int size = parseNumber(lowercase(line).substr(line.find_first_not_of(" \t"), std::string::npos), line);
            if (size < kMinSize || size > kMaxSize) throw std::runtime_error("size must be between 2 and 8");
            cube.emplace(size);
            out << "Starea initiala a cubului Rubik " << size << "x" << size << "x" << size << ":\n" << renderNet(*cube);
            continue;
        }
        const Step step = parseStep(line);
        cube->applyStep(step);
        out << "\nPasul " << ++stepNumber << ": " << formatStep(step) << "\n" << renderNet(*cube);
    }
    if (!cube) throw std::runtime_error("the script must start with the cube size");
}

}  // namespace

int main(int argc, char** argv) {
    try {
        std::ifstream file;
        std::ofstream outFile;
        if (argc > 1) {
            file.open(argv[1]);
            if (!file) throw std::runtime_error(std::string("cannot open ") + argv[1]);
        }
        if (argc > 2) outFile.open(argv[2]);
        run(argc > 1 ? static_cast<std::istream&>(file) : std::cin, argc > 2 ? static_cast<std::ostream&>(outFile) : std::cout);
    } catch (const std::exception& error) {
        std::cerr << "Eroare: " << error.what() << "\n";
        return 1;
    }
    return 0;
}
