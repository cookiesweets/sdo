import m5
from m5.objects import *

# These three directory paths are not currently used.
#gem5_dir = '<FULL_PATH_TO_YOUR_GEM5_INSTALL>'
#spec_dir = '<FULL_PATH_TO_YOUR_SPEC_CPU2006_INSTALL>'
#out_dir = '<FULL_PATH_TO_DESIRED_OUTPUT_DIRECTORY>'

#x86_suffix = '_base.x86_64'
#'_base.my-alpha'
x86_suffix = '_r_base.sparespec-m64'

#temp
#binary_dir = spec_dir
#data_dir = spec_dir

#500.perlbench
perlbench = Process() # Update June 7, 2017: This used to be LiveProcess()
perlbench.executable =  'perlbench' + x86_suffix
# TEST CMDS
#perlbench.cmd = [perlbench.executable] + ['-I.', '-I./lib', 'attrs.pl']
# REF CMDS
perlbench.cmd = [perlbench.executable] + ['-I./lib', 'checkspam.pl', '2500', '5', '25', '11', '150', '1', '1', '1', '1']
#perlbench.cmd = [perlbench.executable] + ['-I./lib', 'diffmail.pl', '4', '800', '10', '17', '19', '300']
#perlbench.cmd = [perlbench.executable] + ['-I./lib', 'splitmail.pl', '1600', '12', '26', '16', '4500']
#perlbench.output = out_dir+'perlbench.out'

#502.gcc
gcc = Process() # Update June 7, 2017: This used to be LiveProcess()
gcc.executable = 'cpugcc' + x86_suffix
# TEST CMDS
#gcc.cmd = [gcc.executable] + ['cccp.i', '-o', 'cccp.s']
# REF CMDS
gcc.cmd = [gcc.executable] + ['gcc-pp.c', '-O3', '-finline-limit=0', '-fif-conversion', '-fif-conversion2', '-o', 'gcc-pp.opts-O3_-finline-limit_0_-fif-conversion_-fif-conversion2.s']
# gcc.cmd = [gcc.executable] + ['166.i', '-o', '166.s']
#gcc.cmd = [gcc.executable] + ['200.i', '-o', '200.s']
#gcc.cmd = [gcc.executable] + ['c-typeck.i', '-o', 'c-typeck.s']
#gcc.cmd = [gcc.executable] + ['cp-decl.i', '-o', 'cp-decl.s']
#gcc.cmd = [gcc.executable] + ['expr.i', '-o', 'expr.s']
#gcc.cmd = [gcc.executable] + ['expr2.i', '-o', 'expr2.s']
#gcc.cmd = [gcc.executable] + ['g23.i', '-o', 'g23.s']
#gcc.cmd = [gcc.executable] + ['s04.i', '-o', 's04.s']
#gcc.cmd = [gcc.executable] + ['scilab.i', '-o', 'scilab.s']
#gcc.output = out_dir + 'gcc.out'

#503.bwaves
bwaves = Process() # Update June 7, 2017: This used to be LiveProcess()
bwaves.executable = 'bwaves' + x86_suffix
# TEST CMDS
#bwaves.cmd = [bwaves.executable]
# REF CMDS
bwaves.cmd = [bwaves.executable] + ['bwaves_1']
bwaves.input = 'bwaves_1.in'
#bwaves.output = out_dir + 'bwaves.out'

#505.mcf
mcf = Process() # Update June 7, 2017: This used to be LiveProcess()
mcf.executable =  'mcf' + x86_suffix
# TEST CMDS
#mcf.cmd = [mcf.executable] + ['inp.in']
# REF CMDS
mcf.cmd = [mcf.executable] + ['inp.in']
#mcf.output = out_dir + 'mcf.out'

#507.cactuBSSN
cactuBSSN = Process() # Update June 7, 2017: This used to be LiveProcess()
cactuBSSN.executable = 'cactusBSSN' + x86_suffix
# TEST CMDS
#cactuBSSN.cmd = [cactuBSSN.executable]
#cactuBSSN.input = 'su3imp.in'
# REF CMDS
cactuBSSN.cmd = [cactuBSSN.executable] + ['spec_ref.par']
# cactuBSSN.input = 'spec_ref.par'
#cactuBSSN.output = out_dir + 'cactuBSSN.out'

#508.namd
namd = Process() # Update June 7, 2017: This used to be LiveProcess()
namd.executable = 'namd' + x86_suffix
# TEST CMDS
#namd.cmd = [namd.executable] + ['--input', 'namd.input', '--output', 'namd.out', '--iterations', '1']
# REF CMDS
namd.cmd = [namd.executable] + ['--input', 'apoa1.input', '--output', 'apoa1.ref.output', '--iterations', '65']
#namd.output = out_dir + 'namd.out'

#510.parest
parest = Process() # Update June 7, 2017: This used to be LiveProcess()
parest.executable = 'parest' + x86_suffix
# TEST CMDS
#parest.cmd = [parest.executable] + ['--input', 'parest.input', '--output', 'parest.out', '--iterations', '1']
# REF CMDS
parest.cmd = [parest.executable] + ['ref.prm']
#parest.output = out_dir + 'parest.out'

#511.povray
povray = Process() # Update June 7, 2017: This used to be LiveProcess()
povray.executable = 'povray' + x86_suffix
# TEST CMDS
#povray.cmd = [povray.executable] + ['SPEC-benchmark-test.ini']
# REF CMDS
povray.cmd = [povray.executable] + ['SPEC-benchmark-ref.ini']
#povray.output = out_dir + 'povray.out'

#519.lbm
lbm = Process() # Update June 7, 2017: This used to be LiveProcess()
lbm.executable = 'lbm' + x86_suffix
# TEST CMDS
#lbm.cmd = [lbm.executable] + ['20', 'reference.dat', '0', '1', '100_100_130_cf_a.of']
# REF CMDS
lbm.cmd = [lbm.executable] + ['3000', 'reference.dat', '0', '0', '100_100_130_ldc.of']
#lbm.output = out_dir + 'lbm.out'

#520.omnetpp
omnetpp = Process() # Update June 7, 2017: This used to be LiveProcess()
omnetpp.executable = 'omnetpp' + x86_suffix
# TEST CMDS
#omnetpp.cmd = [omnetpp.executable] + ['omnetpp.ini']
# REF CMDS
omnetpp.cmd = [omnetpp.executable] + ['-c', 'General', '-r', '0']
#omnetpp.output = out_dir + 'omnetpp.out'

#521.wrf
wrf = Process() # Update June 7, 2017: This used to be LiveProcess()
wrf.executable = 'wrf' + x86_suffix
# TEST CMDS
#wrf.cmd = [wrf.executable]
# REF CMDS
wrf.cmd = [wrf.executable]
#wrf.output = out_dir + 'wrf.out'

#523.xalancbmk
######## NOT WORKING ###########
xalancbmk = Process() # Update June 7, 2017: This used to be LiveProcess()
xalancbmk.executable = 'cpuxalan' + x86_suffix
# TEST CMDS
######## NOT WORKING ###########
xalancbmk.cmd = [xalancbmk.executable] + ['-v','t5.xml','xalanc.xsl']
# REF CMDS
######## NOT WORKING ###########
#xalancbmk.output = out_dir + 'xalancbmk.out'

#525.x264
x264 = Process() # Update June 7, 2017: This used to be LiveProcess()
x264.executable = 'x264' + x86_suffix
# TEST CMDS
#x264.cmd = [x264.executable] + ['test.txt']
# REF CMDS
x264.cmd = [x264.executable] + ['--pass','1','--stats','x264_stats.log','--bitrate','1000','--frames','1000','-o','BuckBunny_New.264','BuckBunny.yuv','1280x720']
#x264.output = out_dir + 'x264.out'

#526.blender
blender = Process() # Update June 7, 2017: This used to be LiveProcess()
blender.executable = 'blender' + x86_suffix
# TEST CMDS
#blender.cmd = [blender.executable] + ['test.txt']
# REF CMDS
blender.cmd = [blender.executable] + ['sh3_no_char.blend','--render-output','sh3_no_char_','--threads','1','-b','-F','RAWTGA','-s','849','-e','849','-a']
#blender.output = out_dir + 'blender.out'

#527.cam4
cam4 = Process() # Update June 7, 2017: This used to be LiveProcess()
cam4.executable = 'cam4' + x86_suffix
# TEST CMDS
#cam4.cmd = [cam4.executable] + ['test.txt']
# REF CMDS
cam4.cmd = [cam4.executable]
#cam4.output = out_dir + 'cam4.out'

#531.deepsjeng
deepsjeng = Process() # Update June 7, 2017: This used to be LiveProcess()
deepsjeng.executable = 'deepsjeng' + x86_suffix
# TEST CMDS
#deepsjeng.cmd = [deepsjeng.executable] + ['test.txt']
# REF CMDS
deepsjeng.cmd = [deepsjeng.executable] + ['ref.txt']
#deepsjeng.output = out_dir + 'deepsjeng.out'

#538.imagick
imagick = Process() # Update June 7, 2017: This used to be LiveProcess()
imagick.executable = 'imagick' + x86_suffix
# TEST CMDS
#imagick.cmd = [imagick.executable] + ['test.txt']
# REF CMDS
imagick.cmd = [imagick.executable] + ['-limit','disk','0','refrate_input.tga','-edge','41','-resample','181%','-emboss','31','-colorspace','YUV','-mean-shift','19x19+15%','-resize','30%','refrate_output.tga']
#imagick.output = out_dir + 'imagick.out'

#541.leela
leela = Process() # Update June 7, 2017: This used to be LiveProcess()
leela.executable = 'leela' + x86_suffix
# TEST CMDS
#leela.cmd = [leela.executable] + ['test.txt']
# REF CMDS
leela.cmd = [leela.executable] + ['ref.sgf']
#leela.output = out_dir + 'leela.out'

#544.nab
nab = Process() # Update June 7, 2017: This used to be LiveProcess()
nab.executable = 'nab' + x86_suffix
# TEST CMDS
#nab.cmd = [nab.executable] + ['test.txt']
# REF CMDS
nab.cmd = [nab.executable] + ['1am0','1122214447','122']
#nab.output = out_dir + 'deepsjeng.out'

#549.fotonik3d
fotonik3d = Process() # Update June 7, 2017: This used to be LiveProcess()
fotonik3d.executable = 'fotonik3d' + x86_suffix
# TEST CMDS
#fotonik3d.cmd = [fotonik3d.executable] + ['test.txt']
# REF CMDS
fotonik3d.cmd = [fotonik3d.executable]
#fotonik3d.output = out_dir + 'deepsjeng.out'

#554.roms
roms = Process() # Update June 7, 2017: This used to be LiveProcess()
roms.executable = 'roms' + x86_suffix
# TEST CMDS
#roms.cmd = [roms.executable] + ['test.txt']
# REF CMDS
roms.cmd = [roms.executable]
roms.input = ['ocean_benchmark2.in.x']
#fotonik3d.output = out_dir + 'deepsjeng.out'

#557.xz
xz = Process() # Update June 7, 2017: This used to be LiveProcess()
xz.executable = 'xz' + x86_suffix
# TEST CMDS
#xz.cmd = [xz.executable] + ['test.txt']
# REF CMDS
xz.cmd = [xz.executable] + ['cld.tar.xz','160','19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474','59796407','61004416','6']
#nab.output = out_dir + 'deepsjeng.out'

# #435.gromacs
# gromacs = Process() # Update June 7, 2017: This used to be LiveProcess()
# gromacs.executable = 'gromacs' + x86_suffix
# # TEST CMDS
# #gromacs.cmd = [gromacs.executable] + ['-silent','-deffnm', 'gromacs', '-nice','0']
# # REF CMDS
# gromacs.cmd = [gromacs.executable] + ['-silent','-deffnm', 'gromacs', '-nice','0']
# #gromacs.output = out_dir + 'gromacs.out'

# #436.cactusADM
# cactusADM = Process() # Update June 7, 2017: This used to be LiveProcess()
# cactusADM.executable = 'cactusADM' + x86_suffix
# # TEST CMDS
# #cactusADM.cmd = [cactusADM.executable] + ['benchADM.par']
# # REF CMDS
# cactusADM.cmd = [cactusADM.executable] + ['benchADM.par']
# #cactusADM.output = out_dir + 'cactusADM.out'

# #437.leslie3d
# leslie3d = Process() # Update June 7, 2017: This used to be LiveProcess()
# leslie3d.executable = 'leslie3d' + x86_suffix
# # TEST CMDS
# #leslie3d.cmd = [leslie3d.executable]
# #leslie3d.input = 'leslie3d.in'
# # REF CMDS
# leslie3d.cmd = [leslie3d.executable]
# leslie3d.input = 'leslie3d.in'
# #leslie3d.output = out_dir + 'leslie3d.out'


# #445.gobmk
# gobmk = Process() # Update June 7, 2017: This used to be LiveProcess()
# gobmk.executable = 'gobmk' + x86_suffix
# # TEST CMDS
# #gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# #gobmk.input = 'dniwog.tst'
# # REF CMDS
# gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# gobmk.input = '13x13.tst'
# #gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# #gobmk.input = 'nngs.tst'
# #gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# #gobmk.input = 'score2.tst'
# #gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# #gobmk.input = 'trevorc.tst'
# #gobmk.cmd = [gobmk.executable] + ['--quiet','--mode', 'gtp']
# #gobmk.input = 'trevord.tst'
# #gobmk.output = out_dir + 'gobmk.out'

# #447.dealII
# ####### NOT WORKING #########
# dealII = Process() # Update June 7, 2017: This used to be LiveProcess()
# dealII.executable = 'dealII' + x86_suffix
# # TEST CMDS
# ####### NOT WORKING #########
# #dealII.cmd = [gobmk.executable]+['8']
# # REF CMDS
# ####### NOT WORKING #########
# #dealII.output = out_dir + 'dealII.out'

# #450.soplex
# soplex = Process() # Update June 7, 2017: This used to be LiveProcess()
# soplex.executable = 'soplex' + x86_suffix
# # TEST CMDS
# #soplex.cmd = [soplex.executable] + ['-m10000', 'test.mps']
# # REF CMDS
# soplex.cmd = [soplex.executable] + ['-m45000', 'pds-50.mps']
# #soplex.cmd = [soplex.executable] + ['-m3500', 'ref.mps']
# #soplex.output = out_dir + 'soplex.out'

# #453.povray
# povray = Process() # Update June 7, 2017: This used to be LiveProcess()
# povray.executable = 'povray' + x86_suffix
# # TEST CMDS
# #povray.cmd = [povray.executable] + ['SPEC-benchmark-test.ini']
# # REF CMDS
# povray.cmd = [povray.executable] + ['SPEC-benchmark-ref.ini']
# #povray.output = out_dir + 'povray.out'

# #454.calculix
# calculix = Process() # Update June 7, 2017: This used to be LiveProcess()
# calculix.executable = 'calculix' + x86_suffix
# # TEST CMDS
# #calculix.cmd = [calculix.executable] + ['-i', 'beampic']
# # REF CMDS
# calculix.cmd = [calculix.executable] + ['-i', 'hyperviscoplastic']
# #calculix.output = out_dir + 'calculix.out'

# #456.hmmer
# hmmer = Process() # Update June 7, 2017: This used to be LiveProcess()
# hmmer.executable = 'hmmer' + x86_suffix
# # TEST CMDS
# #hmmer.cmd = [hmmer.executable] + ['--fixed', '0', '--mean', '325', '--num', '45000', '--sd', '200', '--seed', '0', 'bombesin.hmm']
# # REF CMDS
# hmmer.cmd = [hmmer.executable] + ['nph3.hmm', 'swiss41']
# #hmmer.cmd = [hmmer.executable] + ['--fixed', '0', '--mean', '500', '--num', '500000', '--sd', '350', '--seed', '0', 'retro.hmm']
# #hmmer.output = out_dir + 'hmmer.out'



# #459.GemsFDTD
# GemsFDTD = Process() # Update June 7, 2017: This used to be LiveProcess()
# GemsFDTD.executable = 'GemsFDTD' + x86_suffix
# # TEST CMDS
# #GemsFDTD.cmd = [GemsFDTD.executable]
# # REF CMDS
# GemsFDTD.cmd = [GemsFDTD.executable]
# #GemsFDTD.output = out_dir + 'GemsFDTD.out'

# #462.libquantum
# libquantum = Process() # Update June 7, 2017: This used to be LiveProcess()
# libquantum.executable = 'libquantum' + x86_suffix
# # TEST CMDS
# #libquantum.cmd = [libquantum.executable] + ['33','5']
# # REF CMDS [UPDATE 10/2/2015]: Sparsh Mittal has pointed out the correct input for libquantum should be 1397 and 8, not 1297 and 8. Thanks!
# libquantum.cmd = [libquantum.executable] + ['1397','8']
# #libquantum.output = out_dir + 'libquantum.out'

# #464.h264ref
# h264ref = Process() # Update June 7, 2017: This used to be LiveProcess()
# h264ref.executable = 'h264ref' + x86_suffix
# # TEST CMDS
# #h264ref.cmd = [h264ref.executable] + ['-d', 'foreman_test_encoder_baseline.cfg']
# # REF CMDS
# h264ref.cmd = [h264ref.executable] + ['-d', 'foreman_ref_encoder_baseline.cfg']
# #h264ref.cmd = [h264ref.executable] + ['-d', 'foreman_ref_encoder_main.cfg']
# #h264ref.cmd = [h264ref.executable] + ['-d', 'sss_encoder_main.cfg']
# #h264ref.output = out_dir + 'h264ref.out'

# #465.tonto
# tonto = Process() # Update June 7, 2017: This used to be LiveProcess()
# tonto.executable = 'tonto' + x86_suffix
# # TEST CMDS
# #tonto.cmd = [tonto.executable]
# # REF CMDS
# tonto.cmd = [tonto.executable]
# #tonto.output = out_dir + 'tonto.out'



# #473.astar
# astar = Process() # Update June 7, 2017: This used to be LiveProcess()
# astar.executable = 'astar' + x86_suffix
# # TEST CMDS
# #astar.cmd = [astar.executable] + ['lake.cfg']
# # REF CMDS
# astar.cmd = [astar.executable] + ['rivers.cfg']
# #astar.output = out_dir + 'astar.out'



# #482.sphinx3
# sphinx3 = Process() # Update June 7, 2017: This used to be LiveProcess()
# sphinx3.executable = 'sphinx_livepretend' + x86_suffix
# # TEST CMDS
# #sphinx3.cmd = [sphinx3.executable] + ['ctlfile', '.', 'args.an4']
# # REF CMDS
# sphinx3.cmd = [sphinx3.executable] + ['ctlfile', '.', 'args.an4']
# #sphinx3.output = out_dir + 'sphinx3.out'


# #998.specrand
# specrand_i = Process() # Update June 7, 2017: This used to be LiveProcess()
# specrand_i.executable = 'specrand' + x86_suffix
# # TEST CMDS
# #specrand_i.cmd = [specrand_i.executable] + ['324342', '24239']
# # REF CMDS
# specrand_i.cmd = [specrand_i.executable] + ['1255432124', '234923']
# #specrand_i.output = out_dir + 'specrand_i.out'

# #999.specrand
# specrand_f = Process() # Update June 7, 2017: This used to be LiveProcess()
# specrand_f.executable = 'specrand' + x86_suffix
# # TEST CMDS
# #specrand_f.cmd = [specrand_f.executable] + ['324342', '24239']
# # REF CMDS
# specrand_f.cmd = [specrand_f.executable] + ['1255432124', '234923']
# #specrand_f.output = out_dir + 'specrand_f.out'
