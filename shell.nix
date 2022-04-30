with import <nixpkgs> {};
(python39.withPackages(ps: with ps; [ortools])).env
