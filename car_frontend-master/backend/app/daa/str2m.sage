from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
q=114356107
k=2
d=4
sd=300
M=2.7
sd=3.0
K.<zeta> = CyclotomicField(2*d)
OK = K.ring_of_integers()
sigma=K.automorphisms()
sigma_5=K.hom([zeta^(-1)])
D = DiscreteGaussianDistributionPolynomialSampler(OK, 8, sd)

def str2m(x,dimension):
    y=matrix(dimension, 1, lambda i, j: OK.random_element(16))
    y=y-y
    l=len(x)
    i=0
    d=0
    coe=''
    index=''
    operation='+'
    symbol=x[0]
    print("dimension:",dimension)
    while i < l:     
        print("i:",i)
        print("symbol:",symbol)
        print("d:",d)
     
        if symbol=='[':
            i+=1
            symbol=x[i]
            while symbol==' ':
                i+=1
                symbol=x[i]
            continue
        if(symbol=='+'):
            operation='+'
            i+=1
            symbol=x[i]
        if(symbol=='-'):
            operation='-' 
            i+=1 
            symbol=x[i]
        while '0' <= symbol <= '9':
            coe += symbol
            i+=1
            symbol=x[i]
        if coe!='':
            print("coe:",coe)
        if coe!='' and (symbol==' ' or symbol== ']'):
            if(operation=='+'):
                y[d,0]+=int(coe)
            else:
                y[d,0]+=-int(coe)
            coe=''
        if symbol=='z' or symbol=='e' or symbol=='t' or symbol =='*':
            i+=1
            symbol=x[i]
        if symbol=='a': # if see zeta
            i+=1
            symbol=x[i]
            if symbol == '^':
                i+=1
                symbol=x[i]
                while '0' <= symbol <= '9':
                    index += symbol
                    i+=1
                    symbol=x[i]
            else:
                index='1'
        if (index!= ''): # do have zeta
            print("coe:",coe)
            if(coe==''):
                coe='1'
            if(operation=='+'):
                y[d,0]+=int(coe)*zeta^int(index)
            else:
                y[d,0]+=-int(coe)*zeta^int(index) 
            coe=''
            index=''
        # elif (symbol==']'):
       # elif (symbol!='*'): # no zeta
           # if(coe==''):
              #  coe='0'
           # if(operation=='+'):
              #  y[d,0]+=int(coe)
           # else:
              #  y[d,0]+=-int(coe)
           # coe=''

        if symbol=='\n':
            d+=1
            i+=1
            symbol=x[i]

        if  i<l-1 and symbol==' ' and x[i-1]!= '+' and x[i-1]!='-' and x[i-1] != ' ' and x[i+1]!='+' and x[i+1]!= '-':
            d+=1
          
        if symbol==']':
            if d==dimension-1:
                if coe=='':
                    break
                else:
                    continue
            else:
                i+=1
                symbol=x[i]
                continue  
                
        if symbol==' ':
            i+=1
            symbol=x[i] 
    return y
    
    
a="[         2*zeta^3 + 9*zeta^2 + 9*zeta + 14 zeta^3 + 15*zeta^2 + 15*zeta + 15  11*zeta^3 + 6*zeta^2 + 12*zeta + 8]   " 
b="[ 2*zeta^3 + 9*zeta^2 + 9*zeta + 14]"
c="[14*zeta^3 - zeta^2 + 11*zeta + 13]\n[          -2*zeta^2 + 3*zeta + 16]\n[2*zeta^3 + 9*zeta^2 + 3*zeta + 12]"

print(str2m(a,3))
print(str2m(a,3).transpose())
print(str2m(b,1))
print(str2m(c,3))

