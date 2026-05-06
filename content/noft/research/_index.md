---
title: "Research"
hide_page_hero: true
content_frame: false
hide_child_section: true
weight: 2
---

Natural Orbital Functional Theory (NOFT) is one of the core methodological lines of the NOF-KT group. Its central goal is to recover electron correlation at a computational cost that remains more accessible than highly accurate N-particle wavefunction methods, especially for systems where size or strong correlation make conventional approaches difficult to apply.

## Conceptual basis

The NOFT framework is built on the **one-particle reduced density matrix (1-RDM)** instead of the full many-electron wavefunction or the electron density alone. This choice is scientifically attractive for two main reasons:

- the kinetic energy is available explicitly, so it does not need to be approximated through a separate density functional
- the ensemble **N-representability** conditions of the 1-RDM are well established, providing a rigorous formal foundation

Within this setting, electron correlation is introduced through approximate functionals of the 1-RDM. The spectral expansion of the 1-RDM in terms of natural orbitals and occupation numbers leads to the family of **Natural Orbital Functionals (NOFs)**.

## PNOF and the electron-pairing approach

A major contribution of the group has been the development of the **Piris Natural Orbital Functionals (PNOFs)**. In this line, the cumulant part of the two-particle reduced density matrix is written through auxiliary matrices such as **Delta** and **Pi**, constrained by positivity conditions. This construction enables practical functionals that depend on Coulomb, exchange, and exchange-time-inversion integrals while preserving the physical structure needed to describe both dynamical and nondynamical correlation.

The electron-pairing viewpoint has been especially influential in the NOF-KT program. It provides a transparent framework for building approximate functionals, analyzing their behavior in strongly correlated regimes, and extending them toward open-shell, multiplet, and chemically challenging systems.

## Main research directions

### Approximate natural orbital functionals

The group develops new approximate functionals for the total electronic energy based on natural orbitals and fractional occupations. This includes formal work on the structure of reduced density matrices, N-representability constraints, and the balance between static and dynamic correlation.

### Global descriptions of electron correlation

Beyond the original PNOF family, the subgroup has expanded the framework toward more global descriptions of correlation through **GNOF** and related approximations. These developments target:

- strongly correlated model systems
- delocalization-sensitive problems
- multiplet structure and open-shell chemistry
- chemically demanding applications where correlation balance is decisive

### Post-functional correlation and excited states

Another active area is the coupling of NOF ideas with perturbative and response-theory treatments. This includes **NOF-MP2**, **NOF-MBPT**, and excited-state formalisms that extend the reach of NOFT beyond ground-state energies toward spectroscopy, reactivity, and electronically complex systems.

### Algorithms and numerical efficiency

The NOF-KT group also works on the numerical side of the theory. Relevant directions include:

- orbital optimization strategies
- iterative diagonalization methods
- resolution-of-the-identity approximations
- efficient orbital sorting schemes
- occupation-number parameterizations inspired by modern optimization and machine-learning ideas

These developments are essential for making NOF methods practical for larger systems.

### Quantum-computing-inspired developments

The subgroup has also explored links between reduced-density-matrix methods and quantum algorithms, including **NOF-VQE** strategies aimed at more efficient energy measurements and sampling protocols.

## DoNOF software

The main implementation platform of the subgroup is **DoNOF**, an open-source electronic-structure code devoted to natural-orbital-functional-based methods. It serves both as a research vehicle for methodological development and as a production code for validation, benchmarking, and applications.

Through DoNOF, the NOF-KT group has translated theoretical advances into reproducible computational workflows covering atoms, molecules, and strongly correlated model systems. Recent work has also modernized the codebase and improved its computational efficiency for contemporary research use.

## Representative milestones

### Foundational and perspective works

- M. Piris, [*Natural Orbital Functional Theory*](https://doi.org/10.1002/9780470141731.ch7), *Advances in Chemical Physics* **134**, 387 (2007)
- M. Piris, [*A natural orbital functional based on an explicit approach of the two-electron cumulant*](https://doi.org/10.1002/qua.24305), *Int. J. Quantum Chem.* **113**, 620 (2013)
- M. Piris and J. M. Ugalde, [*Perspective on Natural Orbital Functional Theory*](https://doi.org/10.1002/qua.24712), *Int. J. Quantum Chem.* **114**, 1169 (2014)
- I. Mitxelena, M. Piris, and J. M. Ugalde, [*Advances in Approximate Natural Orbital Functional Theory*](https://doi.org/10.1016/bs.aiq.2019.01.001), *Adv. Quantum Chem.* **79**, 155 (2019)
- M. Piris, [*Advances in Approximate Natural Orbital Functionals: From Historical Perspectives to Contemporary Developments*](https://doi.org/10.1016/bs.aiq.2024.04.002), *Adv. Quantum Chem.* **90**, 15 (2024)
- M. Piris, [*Exploring the Potential of Natural Orbital Functionals*](https://doi.org/10.1039/D4SC05762A), *Chem. Sci.* **15**, 17284 (2024)

### DoNOF and implementation-oriented contributions

- M. Piris and I. Mitxelena, [*DoNOF: an open-source implementation of natural-orbital-functional-based methods for quantum chemistry*](https://doi.org/10.1016/j.cpc.2020.107651), *Comput. Phys. Commun.* **259**, 107651 (2021)
- J. F. H. Lew-Yee, M. Piris, and J. M. del Campo, [*Resolution of the identity approximation applied to PNOF correlation calculations*](https://doi.org/10.1063/5.0037395), *J. Chem. Phys.* **154**, 064102 (2021)
- J. F. H. Lew-Yee, I. Mitxelena, J. M. del Campo, and M. Piris, [*DoNOF 2.0: A modern Open-Source Electronic Structure Program for Natural Orbital Functionals*](https://doi.org/10.1063/5.0278441), *J. Chem. Phys.* **164**, 072501 (2026)

### GNOF and recent functional developments

- M. Piris, [*Global Natural Orbital Functional: Towards the Complete Description of the Electron Correlation*](https://doi.org/10.1103/PhysRevLett.127.233001), *Phys. Rev. Lett.* **127**, 233001 (2021)
- I. Mitxelena and M. Piris, [*Benchmarking GNOF against FCI in challenging systems in one, two and three dimensions*](https://doi.org/10.1063/5.0089283), *J. Chem. Phys.* **156**, 214102 (2022)
- J. F. Huan Lew-Yee, M. Piris, and J. M. del Campo, [*Outstanding Improvement in Removing the Delocalization Error by Global Natural Orbital Functional*](https://doi.org/10.1063/5.0134684), *J. Chem. Phys.* **158**, 084110 (2023)
- J. F. H. Lew-Yee, M. Piris, J. M. del Campo, [*Advancing Natural Orbital Functional Calculations Through Deep Learning-Inspired Techniques for Large-Scale Strongly Correlated Electron Systems*](https://doi.org/10.1103/PhysRevLett.134.206401), *Phys. Rev. Lett.* **134**, 206401 (2025)

### Post-functional correlation and related extensions

- M. Piris, [*Global Method for Electron Correlation*](https://doi.org/10.1103/PhysRevLett.119.063002), *Phys. Rev. Lett.* **119**, 063002 (2017)
- M. Piris, [*Dynamic electron-correlation energy in the NOF-MP2 method from the orbital-invariant perturbation theory*](https://doi.org/10.1103/PhysRevA.98.022504), *Phys. Rev. A* **98**, 022504 (2018)
- M. Rodriguez-Mayorga, I. Mitxelena, F. Bruneval, and M. Piris, [*Coupling Natural Orbital Functional Theory and Many-Body Perturbation Theory by Using Nondynamically Correlated Canonical Orbitals*](https://doi.org/10.1021/acs.jctc.1c00724), *J. Chem. Theory Comput.* **17**, 7562 (2021)
- J. F. H. Lew-Yee, M. Piris, [*Efficient Energy Measurement of Chemical Systems via One-particle Reduced Density Matrix: A NOF-VQE Approach for Optimized Sampling*](https://doi.org/10.1021/acs.jctc.4c01554), *J. Chem. Theory Comput.* **21**, 2402 (2025)

## Current scope of the NOF-KT line

Today, the subgroup combines formal theory, numerical methods, and software development across a coherent set of themes:

- reduced-density-matrix formulations of electronic structure
- design of approximate natural orbital functionals
- strong correlation and delocalization control
- perturbative, excited-state, and multiplet extensions
- scalable implementations in DoNOF
- applications to chemically relevant atoms, molecules, and model systems

This page is an adapted migration of the legacy KT material on Natural Orbital Functional Theory into the structure of the new Hugo site. It preserves the scientific content and main literature landmarks while presenting them in a cleaner page format for the NOF-KT subgroup.
