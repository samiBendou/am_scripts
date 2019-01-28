# am_scripts 0.1.0

General purposes scripts for Airlines-Manager 2 airline management simulation. Theses scripts are designed to help you
to make rational decision while expanding your airline. They give you many indicators and plots to evaluate costs impact
of your decisions.

### Install

**Note** WIP here
Clone the project. You must have matplotlib and numpy libraries installed a python 3.6 environment.

### Getting Started

The script scraps data from airline manager website to provide you usefull informations

#### Demand prevision for opening a new line

If you often ask yourself how much planes and which types should I buy when opening this new line, this script can provide
you a rational evaluation.

Add your hubs onto the `hubs` array and the lines you want to evaluate onto the `lines` array the same way as you've done for
`planes` array.

Run the script, the result of the evalution is displayed on plots and console log.