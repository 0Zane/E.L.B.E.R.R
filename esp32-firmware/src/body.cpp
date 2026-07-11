#include "body.h"

bool isskullopen(){

      if (lox.isRangeComplete()) {
        return lox.readRange() < 30; 
      }
}