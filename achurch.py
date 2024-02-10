from __future__ import annotations
import logging
import pydot
import uuid

from antlr4 import *
from telegram import __version__ as tg_ver
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from dataclasses import dataclass
from lcLexer import lcLexer
from lcParser import lcParser
from lcVisitor import lcVisitor


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@dataclass
class Var:
    val: str


@dataclass
class App:
    t1: Terme
    t2: Terme


@dataclass
class Abs:
    val: str
    body: Terme


Terme = Var | App | Abs


def buildTree(term: Terme, graph: pydot.Dot, boundVariables: dict) -> pydot.Node:
    match term:
        case Var(s):
            node = pydot.Node(name=str(uuid.uuid1()), label=s, shape="plaintext")
            graph.add_node(node)
            if s in boundVariables:
                edgeDash = pydot.Edge(node, boundVariables[s])
                edgeDash.set_style("dashed")
                graph.add_edge(edgeDash)
            return node
        case App(t1, t2):
            node = pydot.Node(name=str(uuid.uuid1()), label="@", shape="plaintext")
            graph.add_node(node)
            secureDict = boundVariables
            t1Node = buildTree(t1, graph, boundVariables)
            graph.add_edge(pydot.Edge(node, t1Node))
            boundVariables = secureDict
            t2Node = buildTree(t2, graph, boundVariables)
            graph.add_edge(pydot.Edge(node, t2Node))
            return node
        case Abs(val, body):
            node = pydot.Node(name=str(uuid.uuid1()), label="λ" + val, shape="plaintext")
            boundVariables[val] = node
            bodyNode = buildTree(body, graph, boundVariables)
            graph.add_node(node)
            graph.add_edge(pydot.Edge(node, bodyNode))
            return node


def generateTree(term: Terme) -> pydot.Dot:
    graph = pydot.Dot(graph_type="digraph")
    buildTree(term, graph, dict())
    return graph


def show(t: Terme) -> str:
    match t:
        case Var(s):
            return s
        case App(t1, t2):
            return "(" + show(t1) + show(t2) + ")"
        case Abs(val, body):
            return "(" + "λ" + val + "." + show(body) + ")"


async def eval(t: Terme, update: Update) -> Tuple[Terme, bool]:
    match t:
        case Var(s):
            return t, False
        case App(t1, t2):
            if isinstance(t1, Abs):
                alphaTreatedT1 = t1
                isModified = True
                alphaTreatedT1, isModified = await alphaConversion(t1, t2, update)
                betaReducedTerm = betaSubstitute(alphaTreatedT1, t1.val, t2)
                await update.message.reply_text(show(App(alphaTreatedT1, t2)) + " →β→ " + show(betaReducedTerm))
                return betaReducedTerm, True
            else:
                newT1, isModified = await eval(t1, update)
                if isModified:
                    return App(newT1, t2), True
                else:
                    newT2, isModified = await eval(t2, update)
                    return App(t1, newT2), isModified
        case Abs(val, body):
            newBody, isModified = await eval(body, update)
            return Abs(val, newBody), isModified


def betaSubstitute(term: Terme, variable: string, replacement: Terme) -> Terme:
    match term:
        case Var(s):
            if s == variable:
                return replacement
            else:
                return term
        case App(t1, t2):
            newT1 = betaSubstitute(t1, variable, replacement)
            newT2 = betaSubstitute(t2, variable, replacement)
            return App(newT1, newT2)
        case Abs(val, body):
            if val == variable:
                return betaSubstitute(body, variable, replacement)
            else:
                newBody = betaSubstitute(body, variable, replacement)
                return Abs(val, newBody)


async def alphaConversion(t1: Terme, t2: Terme, update: Update) -> Tuple[Terme, bool]:
    usedVariables = getUsedVariables(t2)
    boundVariables = getBoundVariables(t1)
    newVar = findNewVariable(boundVariables | usedVariables)
    newTerm, isModified = searchReplacement(t1, t1.val, newVar, usedVariables.difference({t1.val}))
    if isModified:
        await update.message.reply_text(show(t1) + " →α→ " + show(newTerm))
    return newTerm, isModified


def getUsedVariables(term: Terme) -> set[string]:
    match term:
        case Var(s):
            return {s}
        case App(t1, t2):
            return getUsedVariables(t1) | getUsedVariables(t2)
        case Abs(val, body):
            return {val} | getUsedVariables(body)


def getBoundVariables(term: Terme) -> set[string]:
    match term:
        case Var(s):
            return set()
        case App(t1, t2):
            return getBoundVariables(t1) | getBoundVariables(t2)
        case Abs(val, body):
            return {val} | getBoundVariables(body)


def searchReplacement(term: Terme, varToReplace: string, replacement: string, usedVariables: set[string]) -> Tuple[Terme, bool]:
    match term:
        case Var(s):
            return term, False
        case App(t1, t2):
            newT1, isModified1 = searchReplacement(t1, varToReplace, replacement, usedVariables)
            newT2, isModified2 = searchReplacement(t2, varToReplace, replacement, usedVariables)
            return App(newT1, newT2), isModified1 or isModified2
        case Abs(val, body):
            if val in usedVariables and varToReplace in getUsedVariables(body):
                newBody, isModified = replaceVar(body, val, replacement)
                return Abs(replacement, newBody), True
            else:
                newBody, isModified = searchReplacement(body, varToReplace, replacement, usedVariables)
                return Abs(val, newBody), isModified


def replaceVar(term: Terme, var: string, newVar: string) -> Tuple[Terme, bool]:
    match term:
        case Var(s):
            if s == var:
                return Var(newVar), True
            else:
                return term, False
        case App(t1, t2):
            newT1, isModified1 = replaceVar(t1, var, newVar)
            newT2, isModified2 = replaceVar(t2, var, newVar)
            return App(newT1, newT2), isModified1 or isModified2
        case Abs(val, body):
            if val == var:
                newBody, isModified = replaceVar(body, var, newVar)
                return Abs(newVar, newBody), True
            else:
                newBody, isModified = replaceVar(body, var, newVar)
                return Abs(val, newBody), isModified


def findNewVariable(usedVariables: set) -> string:
    for var in "abcdefghijklmnopqrstuvwxyz":
        if var not in usedVariables:
            return var


class TreeVisitor(lcVisitor):
    def visitRoot(self, ctx):
        [terme] = list(ctx.getChildren())
        return self.visit(terme)

    def visitVar(self, ctx):
        [lletra] = list(ctx.getChildren())
        return Var(lletra.getText())

    def visitTermePar(self, ctx):
        [par1, terme, par2] = list(ctx.getChildren())
        return self.visit(terme)

    def visitAplicacio(self, ctx):
        [terme1, terme2] = list(ctx.getChildren())
        return App(self.visit(terme1), self.visit(terme2))

    def visitAbstraccio(self, ctx):
        [lamda, lletres, punt, terme] = list(ctx.getChildren())
        t = self.visit(terme)
        for lletra in reversed(self.visit(lletres)):
            t = Abs(lletra, t)
        return t

    def visitLletres(self, ctx):
        lletres = list(ctx.getChildren())
        auxStr = ""
        for lletra in lletres:
            auxStr += lletra.getText()
        return auxStr

    def visitMacroTerme(self, ctx):
        [macro] = list(ctx.getChildren())
        return self.macros[macro.getText()]

    def visitOperacioInfixa(self, ctx):
        [terme1, operador, terme2] = list(ctx.getChildren())
        t1 = self.visit(terme1)
        t2 = self.visit(terme2)
        termeOp = self.macros[operador.getText()]
        return App(App(termeOp, t1), t2)

    def visitMacro(self, ctx):
        [macro, eq, term] = list(ctx.getChildren())
        self.macros[macro.getText()] = self.visit(term)
        return self.macros

    def visitInfijo(self, ctx):
        [operador, eq, term] = list(ctx.getChildren())
        self.macros[operador.getText()] = self.visit(term)
        return self.macros


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    context.user_data["macros"] = dict()
    await update.message.reply_html(
        "AChurchBot!\n" + rf"Benvingut {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/start\n/author\n/help\n/macros\nExpressió λ-càlcul")


async def author_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("AChurchBot!\n@ Albert Ruiz Vives, 2023",)


async def macros_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    expr = context.user_data["macros"]
    textMssg = ""
    for key in expr:
        textMssg += key + " ≡ " + show(expr[key]) + "\n"
    if textMssg == "":
        await update.message.reply_text("No macros defined!")
    else:
        await update.message.reply_text(textMssg)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    visitor = TreeVisitor()
    visitor.macros = context.user_data["macros"]
    lexer = lcLexer(InputStream(update.message.text))
    token_stream = CommonTokenStream(lexer)
    parser = lcParser(token_stream)
    tree = parser.root()

    expr = visitor.visit(tree)
    if(isinstance(expr, Terme)):
        await update.message.reply_text(show(expr))
        graph = generateTree(expr)
        graph.write_png("graph.png")
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("graph.png", "rb"))
        cont = 0
        while cont < 50:
            expr, isModified = await eval(expr, update)
            if(isModified):
                cont = cont + 1
            else:
                break

        if cont == 50:
            await update.message.reply_text("Nothing")
        else:
            await update.message.reply_text(show(expr))
            graph = generateTree(expr)
            graph.write_png("graph.png")
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("graph.png", "rb"))
    else:
        context.user_data["macros"] = expr


def main() -> None:

    application = Application.builder().token("6174998347:AAFlg58t0PyGodcoNrdogMam2ZP6npYEvI4").build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(CommandHandler("author", author_command))

    application.add_handler(CommandHandler("macros", macros_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":

    main()
