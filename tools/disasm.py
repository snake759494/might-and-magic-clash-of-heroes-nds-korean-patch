import sys
from capstone import *
d=open('work/arm9.bin','rb').read()
a=int(sys.argv[1],16); n=int(sys.argv[2],0); mode=CS_MODE_THUMB if len(sys.argv)>3 else CS_MODE_ARM
md=Cs(CS_ARCH_ARM,mode)
for i in md.disasm(d[a-0x2000000:a-0x2000000+n],a): print(hex(i.address),i.mnemonic,i.op_str)
