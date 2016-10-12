extern "C" {  
        int _classify_skin(int r, int g, int b) {
        	double cb = 128 - 0.168736*r - 0.331364*g + 0.5*b;
			double cr = 128 + 0.5*r - 0.418688*g - 0.081312*b;
        	if (97.5 <= cb && cb <= 142.5 && 134 <= cr && cr <= 176)
    			return 1;
    		return 0;
        }  
}  