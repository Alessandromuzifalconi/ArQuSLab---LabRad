import pyvisa

rm = pyvisa.ResourceManager()
inst = rm.open_resource('ASRL3::INSTR')

print(inst)

print(inst.query('dds reset'))
for i in range(20):
    print(inst.query('dcp 0 spi:cfr2=0x010000'))
print(inst.query('dcp 0 spi:stp0=0x3fff00002147ae14'))
print(inst.query('dcp update:u'))
print(inst.query('dcp start'))

inst.close()