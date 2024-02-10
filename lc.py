from __future__ import annotations
from dataclasses import dataclass
from antlr4 import *
from lcLexer import lcLexer
from lcParser import lcParser
from lcVisitor import lcVisitor

@dataclass
class Var:
    val: string

@dataclass
class App:
    t1: Terme
    t2: Terme

@dataclass
class Abs:
    val: string
    body: Terme

Terme = Var | App | Abs

def show(t: Terme) -> string:
    match t:
        case Var(s):
            return s
        case App(t1, t2):
            return "(" + show(t1) + show(t2) + ")"
        case Abs(val, body):
            return "(" + "λ" + val + "." + show(body) +     ")"
        
def eval(t: Terme) -> Tuple[Terme, bool]:
    match t:
        case Var(s):
            return t, False
        case App(t1, t2):
            if isinstance(t1, Abs):
                alphaTreatedT1 = t1
                isModified = True
                #while isModified:
                alphaTreatedT1, isModified = alphaConversion(t1, t2)
                betaReducedTerm = betaSubstitute(alphaTreatedT1, t1.val, t2)
                print ("β-reducció:")
                print (show(App(alphaTreatedT1, t2)) + " → " + show(betaReducedTerm))
                return betaReducedTerm, True
            else:
                newT1, isModified = eval(t1)
                if isModified:
                    return App(newT1, t2), True
                else:
                    newT2, isModified = eval(t2)
                    return App(t1, newT2), isModified
        case Abs(val, body):
            newBody, isModified = eval(body)
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

def alphaConversion(t1: Terme, t2: Terme) -> Tuple[Terme, bool]:
    usedVariables = getUsedVariables(t2)
    boundVariables = getBoundVariables(t1)
    newVar = findNewVariable(boundVariables | usedVariables)
    newTerm, isModified = searchReplacement(t1, t1.val, newVar, usedVariables.difference({t1.val}))
    if isModified:
        print (show(t1) + " → " + show(newTerm))
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
                print("α-conversió: " + val + " → " + replacement)
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
    def __init__(self):
        self.macros = {}

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
        

visitor = TreeVisitor()
input_stream = InputStream(input('? '))
while input_stream:
    lexer = lcLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = lcParser(token_stream)
    tree = parser.root()

    expr = visitor.visit(tree)
    if(isinstance(expr, Terme)):
        print("Arbre:")
        print(show(expr)) 

        cont = 0
        while cont < 10:
            expr, isModified = eval(expr)
            if(isModified):
                cont = cont + 1
            else:
                break

        print("Resultat:")
        if cont == 10:
            print("Nothing")
        else:
            print(show(expr))
    else:
        for key in expr:
            print(key + " ≡ " + show(expr[key]))

    input_stream = InputStream(input('? '))


#print(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
#print(tree.toStringTree(recog=parser))