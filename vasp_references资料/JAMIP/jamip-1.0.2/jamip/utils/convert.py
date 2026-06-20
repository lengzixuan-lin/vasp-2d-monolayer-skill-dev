
def str2latex(kpt):
    latex = ['alpha','beta','gamma','delta','epsilon','varepsilon','zeta','eta',
             'theta','vartheta','iota','kappa','lambda','mu','nu','xi','pi','varpi',
             'rho','varrho','sigma','varsigma','tau','upsilon','phi','varphi',
             'chi','psi','omega']
    if kpt.lower() in latex:
        return '\\'+kpt.capitalize()
    else:
        return kpt

def kpath2list(kpath):
    klist = []

    def kprint(k1,k2=None):
        if len(k1) > 1:
            k1 = str2latex(k1)
            if '\\' in k1: k1='$'+k1
            else: k1 = '${0}_{1}'.format(k1[0],k1[1:])
        if k2:
            if len(k2) > 1:
                k2 = str2latex(k2)
                if k1[0]!='$': k1='$'+k1
                if '\\' in k2: k1='{0}|{1}'.format(k1,k2)
                else: k1 = '{0}|{1}_{2}'.format(k1,k2[0],k2[1:])
            else: k1='{0}|{1}'.format(k1,k2)
        if k1[0] == '$': k1=k1+'$'
        klist.append(k1)

    for index,kp in enumerate(kpath):
        if index == 0: kprint(kp[0])
        for k in kp[1:-1]:
            kprint(k)
        if index < len(kpath)-1:
            kprint(kp[-1],kpath[index+1][0])
        else:
            kprint(kp[-1])
    return klist 
