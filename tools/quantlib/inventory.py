# Inventory of QuantLib-Python classes, used to build the Model library.
# Run: pip install QuantLib && python3 tools/quantlib/inventory.py (writes inventory.json next to it).
# Not deployed: Vercel only serves public/.
import QuantLib as ql, inspect, json, re
classes={n:getattr(ql,n) for n in dir(ql) if inspect.isclass(getattr(ql,n)) and not n.startswith('_')}
def subs(base):
    b=getattr(ql,base,None)
    return sorted(n for n,c in classes.items() if b and c is not b and issubclass(c,b))
out={}
for base in ['CalibratedModel','StochasticProcess','PricingEngine','Calendar','DayCounter','YieldTermStructure','DefaultProbabilityTermStructure','BlackVolTermStructure','LocalVolTermStructure','SwaptionVolatilityStructure','OptionletVolatilityStructure','Instrument','IborIndex','OvernightIndex','SmileSection']:
    out[base]=subs(base)
    print(base, len(out[base]))
out['BusinessDayConvention']=[n for n in ['Following','ModifiedFollowing','Preceding','ModifiedPreceding','Unadjusted','HalfMonthModifiedFollowing','Nearest'] if hasattr(ql,n)]
out['functions']=sorted(n for n in dir(ql) if re.search(r'(sabr|svi|blackFormula|bachelier|Volatility$)',n) and callable(getattr(ql,n)) and not inspect.isclass(getattr(ql,n)))
out['version']=ql.__version__
json.dump(out,open(__import__('os').path.join(__import__('os').path.dirname(__file__),'inventory.json'),'w'),indent=1)
print('models:',out['CalibratedModel'])
print('processes:',out['StochasticProcess'])
