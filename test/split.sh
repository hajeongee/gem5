rm -rf splitsim m5out*
mkdir -p splitsim
../build/X86/gem5.opt -d m5out-main \
  ../configs/simbricks/splitsim-fs.py \
  split-main 2>&1 | tee main.log &
sleep 5

../build/X86/gem5.opt -d m5out-c0 \
  ../configs/simbricks/splitsim-fs.py \
  split-core0 2>&1 | tee c0.log &

sleep 5

../build/X86/gem5.opt -d m5out-c1 \
  ../configs/simbricks/splitsim-fs.py \
  split-core1 2>&1 | tee c1.log

sleep 5
