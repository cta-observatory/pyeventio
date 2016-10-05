# coding: utf-8
import eventio
path = 'eventio/resources/one_shower.dat'
f = open(path, 'rb')
size = f.seek(0, 2)
f.seek(0)

obs = eventio.objects(f)
obs[5]
o = obs[5]
start_address = sum(h.data_field_first_byte for h in o.headers)


