CXXFLAGS =	-O2 -flto -g -Wall -fmessage-length=0 -std=c++11 -I/home/cbuck/net/build/gumbo/include/ -I/home/cbuck/net/build/cld2/public/
LDFLAGS = -flto -O2 -static 
LIBS = -L/home/cbuck/net/build/gumbo/lib/ -L/home/cbuck/net/build/cld2/internal/  

OBJS =		html2text.o langsplit.o
HEADERS =	*.h

default: all


TARGET =	html2text langsplit

#html2text:	html2text.o
#	$(CXX) -o html2text.o $(OBJS) $(LDFLAGS) $(LIBS)
#
#
#$(TARGET):	$(OBJS)
#	$(CXX) -o $(TARGET) $(OBJS) $(LDFLAGS) $(LIBS)

html2text: html2text.o
	$(CXX) -o $@ $^ $(LDFLAGS) -lgumbo $(LIBS)

langsplit: langsplit.o
	$(CXX) -o $@ $^ $(LDFLAGS) -lcld2_full $(LIBS)
	
%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c $< -o $@  


.PHONY : all clean
all:	html2text langsplit

clean:
	rm -f $(OBJS) $(TARGET)
