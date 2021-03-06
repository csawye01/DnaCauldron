import flametree # for getting/writing files and folders
from Bio import SeqIO  # for exporting to Genbank
from dnacauldron import RestrictionLigationMix, load_genbank

root = flametree.file_tree('.')
parts = [
    load_genbank(f._path, linear=False)
    for f in root.data.assemblies._all_files
]
mix = RestrictionLigationMix(parts, enzyme='BsmBI')
assemblies_records = mix.compute_circular_assemblies()
output_folder = root._dir('output_data')._dir('combinatorial_assemblies')
for i, record in enumerate(assemblies_records):
    SeqIO.write(record, output_folder._file("assembly_%03d.gb" % i), "genbank")
print ("%d combinatorial assembly genbanks written in output_data/assemblies"
       % (i + 1))
