import java.util.*;
import java.util.regex.*;

public class Parser {
    private static class Token {
        String type;
        String value;

        Token(String type, String value) {
            this.type = type;
            this.value = value;
        }

        @Override
        public String toString() {
            return type + "(" + value + ")";
        }
    }

    private static class Lexer {
        private static class TokenRule {
            String type;
            Pattern pattern;

            TokenRule(String type, String regex) {
                this.type = type;
                this.pattern = Pattern.compile("^(" + regex + ")");
            }
        }

        private final List<TokenRule> tokenRules = new ArrayList<>();
        private final List<Pattern> skipPatterns = new ArrayList<>();

        public void addToken(String type, String regex) {
            tokenRules.add(new TokenRule(type, regex));
        }

        public void skip(String regex) {
            skipPatterns.add(Pattern.compile("^(" + regex + ")"));
        }

        public List<Token> tokenize(String input) {
            List<Token> tokens = new ArrayList<>();
            while (!input.isEmpty()) {
                boolean matched = false;
                for (Pattern skipPattern : skipPatterns) {
                    Matcher matcher = skipPattern.matcher(input);
                    if (matcher.find()) {
                        input = input.substring(matcher.end());
                        matched = true;
                        break;
                    }
                }
                if (matched) continue;

                for (TokenRule rule : tokenRules) {
                    Matcher matcher = rule.pattern.matcher(input);
                    if (matcher.find()) {
                        tokens.add(new Token(rule.type, matcher.group(1)));
                        input = input.substring(matcher.end());
                        matched = true;
                        break;
                    }
                }
                if (!matched) {
                    throw new IllegalArgumentException(
                        "Unexpected character: " + input.charAt(0));
                }
            }
            return tokens;
        }
    }

    private static class ParserException extends RuntimeException {
        ParserException(String message) {
            super(message);
        }
    }

    private static class Node {
        String type;
        List<Node> children;
        String value;

        Node(String type) {
            this(type, null);
        }

        Node(String type, String value) {
            this.type = type;
            this.value = value;
            this.children = new ArrayList<>();
        }

        void addChild(Node child) {
            children.add(child);
        }

        @Override
        public String toString() {
            if (value != null) {
                return type + "(" + value + ")";
            } else {
                StringBuilder sb = new StringBuilder(type + "(");
                for (Node child : children) {
                    sb.append(child.toString()).append(", ");
                }
                if (!children.isEmpty()) {
                    sb.setLength(sb.length() - 2);
                }
                sb.append(")");
                return sb.toString();
            }
        }
    }

    private final List<Token> tokens;
    private int position;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
        this.position = 0;
    }

    private Token match(String type) {
        if (position < tokens.size() && tokens.get(position).type.equals(type)) {
            return tokens.get(position++);
        }
        throw new ParserException("Expected token " + type + " at position " + position);
    }

    private boolean lookahead(String type) {
        return position < tokens.size() && tokens.get(position).type.equals(type);
    }

    private Node expr() {
        return plus();
    }

    private Node plus() {
        Node node = mult();
        if (lookahead("+")) {
            Node plusNode = new Node("Plus");
            plusNode.addChild(node);
            match("+");
            plusNode.addChild(mult());
            return plusNode;
        }
        return node;
    }

    private Node mult() {
        Node node = atom();
        if (lookahead("*")) {
            Node multNode = new Node("Mult");
            multNode.addChild(node);
            match("*");
            multNode.addChild(atom());
            return multNode;
        }
        return node;
    }

    private Node atom() {
        if (lookahead("INT")) {
            return new Node("Int", match("INT").value);
        }
        if (lookahead("IDENTIFIER")) {
            return call();
        }
        throw new ParserException("Expected INT or IDENTIFIER at position " + position);
    }

    private Node call() {
        Node callNode = new Node("Call");
        callNode.addChild(new Node("Identifier", match("IDENTIFIER").value));
        match("(");
        callNode.addChild(expr());
        match(")");
        return callNode;
    }
    public class Codegen {
        public static class CNode {
            String type;
            String value;
            List<CNode> children;

            CNode(String type) {
                this(type, null);
            }

            CNode(String type, String value) {
                this.type = type;
                this.value = value;
                this.children = new ArrayList<>();
            }

            void addChild(CNode child) {
                children.add(child);
            }

            @Override
            public String toString() {
                if (value != null) {
                    return type + "(" + value + ")";
                } else {
                    StringBuilder sb = new StringBuilder(type + "(");
                    for (CNode child : children) {
                        sb.append(child.toString()).append(", ");
                    }
                    if (!children.isEmpty()) {
                        sb.setLength(sb.length() - 2);
                    }
                    sb.append(")");
                    return sb.toString();
                }
            }
        }

        public CNode transform(Node node) {
            switch (node.type) {
                case "Plus":
                    CNode plusNode = new CNode("Plus");
                    for (Node child : node.children) {
                        plusNode.addChild(transform(child));
                    }
                    return plusNode;
                case "Mult":
                    CNode multNode = new CNode("Mult");
                    for (Node child : node.children) {
                        multNode.addChild(transform(child));
                    }
                    return multNode;
                case "Int":
                    return new CNode("Int", node.value);
                case "Call":
                    CNode callNode = new CNode("Call");
                    callNode.addChild(new CNode("Identifier", node.children.get(0).value));
                    callNode.addChild(transform(node.children.get(1)));
                    return callNode;
                default:
                    throw new IllegalArgumentException("Unknown node type: " + node.type);
            }
        }

        public String generateCode(CNode node) {
            switch (node.type) {
                case "Plus":
                    return generateCode(node.children.get(0)) + " + " +
                        generateCode(node.children.get(1));
                case "Mult":
                    return generateCode(node.children.get(0)) + " * " +
                        generateCode(node.children.get(1));
                case "Int":
                    return node.value;
                case "Call":
                    String functionName = node.children.get(0).value;
                    if (functionName.equals("print")) {
                        return "printf(\"%d\\n\", " +
                            generateCode(node.children.get(1)) + ")";
                    } else {
                        return functionName + "(" +
                            generateCode(node.children.get(1)) + ")";
                    }
                default:
                    throw new IllegalArgumentException(
                        "Unknown CNode type: " + node.type);
            }
        }

        public String generateMain(CNode node) {
            return "#include <stdio.h>\n\nint main() {\n    " +
                generateCode(node) + ";\n    return 0;\n}";
        }

        public static void main(String[] args) {
            Lexer lexer = new Lexer();
            lexer.addToken("INT", "\\d+");
            lexer.addToken("IDENTIFIER", "[a-zA-Z_][a-zA-Z_0-9]*");
            lexer.addToken("+", "\\+");
            lexer.addToken("*", "\\*");
            lexer.addToken("(", "\\(");
            lexer.addToken(")", "\\)");
            lexer.skip("\\s+");

            String input = "print(34 + 17 * foo(2))";
            List<Token> tokens = lexer.tokenize(input);
            Parser parser = new Parser(tokens);
            Node parseTree = parser.expr();
            System.out.println("Parse Tree: " + parseTree);

            Codegen codegen = new Codegen();
            CNode cTree = codegen.transform(parseTree);
            System.out.println("C Tree: " + cTree);

            String code = codegen.generateMain(cTree);
            System.out.println("Generated C Code:\n" + code);
        }
    }
}
