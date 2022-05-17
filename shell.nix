with import <nixpkgs> {};
(python39.withPackages(ps: with ps; [
ortools
dataclasses-json
networkx])).env
