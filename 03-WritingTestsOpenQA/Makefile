ELEMENTNAME=workshop

all: doc clean

doc: $(ELEMENTNAME).tex 
	pdflatex $(ELEMENTNAME).tex && pdflatex $(ELEMENTNAME).tex

clean:
	rm -rf *.{aux,toc,log,out,snm,nav,lot,lol,lof}
	rm -rf *~
