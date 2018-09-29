import subprocess
import os
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("target_executable")
  parser.add_argument("destination_dir")
  args = parser.parse_args()
  
  target = bytes(args.target_executable, 'utf-8')
  output_dir = bytes(args.destination_dir, 'utf-8')

  try:
    os.mkdir(output_dir)
  except FileExistsError:
    pass

  q = ["cp", target, output_dir]
  subprocess.check_call(q)

  targets_todo = [os.path.join(output_dir, target)]
  targets_done = []

  while len(targets_todo)>0:
    current_target = targets_todo.pop()
    otool_out = subprocess.check_output(["otool", "-L", current_target])
    print("Scanning dependencies of {}".format(current_target))

    for libline in otool_out.splitlines()[1:]:
      libpath = libline.split()[0]

      if os.path.basename(libpath) == os.path.basename(current_target):
        continue
      if libpath.startswith(b"@"):
        continue
      if libpath.startswith(b"/usr/lib/"):
        continue
      if libpath.startswith(b"/System/"):
        continue
      if os.path.basename(libpath) in targets_done:
        print("\tFixing reference to {}".format(os.path.basename(libpath)))
        q = ["install_name_tool", "-change", libpath, os.path.join(b"@executable_path", os.path.basename(libpath)), os.path.join(output_dir, os.path.basename(current_target))]
        subprocess.check_call(q)
        continue

      print("\tRelocating {}".format(libpath))
      q = ["cp", libpath, output_dir]
      subprocess.check_call(q)

      new_libpath = os.path.join(output_dir, os.path.basename(libpath))
      q = ["chmod", "u+w", new_libpath]
      subprocess.check_call(q)
      
      q = ["install_name_tool", "-change", libpath, os.path.join(b"@executable_path", os.path.basename(libpath)), os.path.join(output_dir, os.path.basename(current_target))]
      subprocess.check_call(q)
      
      targets_todo.append(new_libpath)
    
    targets_done.append(os.path.basename(current_target))
