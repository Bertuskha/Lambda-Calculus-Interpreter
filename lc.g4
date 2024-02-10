grammar lc;

root 
    : terme             // l'etiqueta ja és root
    | macro
    | infijo
    ;    

macro : MACRO ('='|'≡') terme;
infijo: OP ('='|'≡') terme;

terme
    : '(' terme ')'                 #termePar
    | terme terme                   #aplicacio
    | LAMBDA lletres '.' terme      #abstraccio
    | terme OP terme                #operacioInfixa
    | LLETRA                        #var
    | MACRO                         #macroTerme
    ;

lletres
    : (LLETRA)+
    ;

MACRO : [A-Z][A-Z0-9]*;
OP: ('~'|'`'|'{'|'}'|'['|']'|'!'|'%'|'^'|'*'|'-'|'='|'+'|'_'|'|'|'@'|':'|';'|'<'|'>'|'?'|'.'|','|'#'|'&'|'$'|'('|')');
LLETRA : ('a'..'z') ;
LAMBDA : ('λ'|'\\') ;
WS  : [ \t\n\r]+ -> skip ;