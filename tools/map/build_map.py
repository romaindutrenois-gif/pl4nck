# Build public/map.json for the model map.
#
# Inputs
#   tools/map/core.json          curated layer: Veqctor nodes, lanes, roadmap edges, quantum layer
#   tools/quantlib/inventory.json  Python-exposed QuantLib classes (tools/quantlib/inventory.py)
#   tools/quantlib/links.json      QuantLib links from the C++ and SWIG sources (tools/quantlib/links.py)
# Output
#   public/map.json  clouds, folded nodes (one node per concept, QuantLib classes listed as variants), edges
#
# Run: python3 tools/map/build_map.py
import json, os, re
from collections import defaultdict, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
core = json.load(open(os.path.join(ROOT, 'tools/map/core.json')))
inv = json.load(open(os.path.join(ROOT, 'tools/quantlib/inventory.json')))
links = json.load(open(os.path.join(ROOT, 'tools/quantlib/links.json')))['classes']

CLOUDS = [
    ('conv', 'Conventions and indexes', 'Calendars, day counts, schedules and the rate indexes everything else fixes against.'),
    ('curves', 'Yield and credit curves', 'Discount, forward and default curves: bootstrapping, interpolation, spreads.'),
    ('vol', 'Volatility', 'Implied surfaces, local volatility, swaption and caplet volatility, smile sections.'),
    ('models', 'Models and processes', 'The dynamics: each node folds the QuantLib model and its stochastic process.'),
    ('methods', 'Numerical methods', 'Monte Carlo, trees, finite differences, Fourier, regression, calibration, AAD.'),
    ('engines', 'Pricing engines', 'One engine prices one instrument under one model with one method.'),
    ('instruments', 'Instruments', 'Products, grouped by family.'),
    ('risk', 'Risk, portfolio and XVA', 'Portfolio-level measures and optimisation built on top of pricing.'),
    ('quantum', 'Quantum algorithms', 'The quantum layer and the classical models each algorithm builds on.'),
]

nodes = OrderedDict()
def add(id, name, cloud, group=None, **kw):
    n = nodes.setdefault(id, {'id': id, 'name': name, 'cloud': cloud})
    n.update({k: v for k, v in kw.items() if v is not None})
    if group: n['group'] = group
    return n

# ---------- 1. curated layer (roadmap and quantum views use only these: core = true)
CORE_CLOUD = {
    'conv': ('conv', 'Conventions'), 'curve': ('curves', 'Bootstrapped curves'), 'volsurf': ('vol', 'Equity and FX'),
    'mcengine': ('methods', 'Monte Carlo'), 'vr': ('methods', 'Monte Carlo'), 'qmc': ('methods', 'Monte Carlo'),
    'aad': ('methods', 'Sensitivities and hardware'), 'gpu': ('methods', 'Sensitivities and hardware'),
    'bs': ('models', 'Equity and FX'), 'lv': ('models', 'Equity and FX'), 'heston': ('models', 'Equity and FX'),
    'bates': ('models', 'Equity and FX'), 'slv': ('models', 'Equity and FX'), 'merton': ('models', 'Equity and FX'),
    'shortrate': ('models', 'Rates'), 'black': ('models', 'Rates'), 'hw': ('models', 'Rates'), 'sabr': ('models', 'Rates'),
    'g2': ('models', 'Rates'), 'lmm': ('models', 'Rates'),
    'cds': ('curves', 'Credit curves'), 'copula': ('models', 'Credit'), 'cpm': ('risk', 'Credit risk'),
    'hvar': ('risk', 'Market risk'), 'garch': ('models', 'Volatility dynamics'), 'mcvar': ('risk', 'Market risk'),
    'mv': ('risk', 'Portfolio'), 'card': ('risk', 'Portfolio'), 'gen': ('risk', 'Portfolio'),
    'pfe': ('risk', 'Counterparty risk'),
}
for n in core['nodes']:
    if n.get('quantum'):
        cloud, group = 'quantum', 'Quantum algorithms'
    else:
        cloud, group = CORE_CLOUD[n['id']]
    add(n['id'], n['name'], cloud, group, core=True, lane=n['lane'], coverage=n.get('coverage'),
        quantum=n.get('quantum'), library=n.get('library'), note=n.get('note'))

# QuantLib classes folded into the curated nodes, and renames where QuantLib adds scope
FOLD_CORE = {
    'conv': {'variants': ['Calendars: ' + ', '.join(inv['Calendar']), 'Day counts: ' + ', '.join(inv['DayCounter']),
                          'Business-day conventions: ' + ', '.join(inv['BusinessDayConvention']), 'Schedule'],
             'ql': ['Calendar', 'DayCounter', 'BusinessDayConvention', 'Schedule']},
    'bs': {'ql': ['GeneralizedBlackScholesProcess', 'BlackScholesProcess', 'BlackScholesMertonProcess', 'BlackProcess',
                  'GarmanKohlagenProcess', 'GeometricBrownianMotionProcess', 'StochasticProcessArray'],
           'variants': ['Black-Scholes-Merton (dividend yield)', 'Black (futures)', 'Garman-Kohlhagen (FX)', 'Multi-asset (process array)']},
    'heston': {'ql': ['HestonModel', 'HestonProcess']},
    'bates': {'ql': ['BatesModel', 'BatesProcess']},
    'slv': {'ql': ['HestonSLVProcess']},
    'merton': {'ql': ['Merton76Process']},
    'lv': {'ql': ['GridModelLocalVolSurface']},
    'shortrate': {'ql': ['Vasicek', 'CoxIngersollRoss', 'ExtendedCoxIngersollRoss'], 'variants': ['Vasicek', 'CIR', 'Extended CIR (fitted to the curve)']},
    'hw': {'ql': ['HullWhite', 'HullWhiteProcess', 'HullWhiteForwardProcess']},
    'g2': {'ql': ['G2', 'G2Process', 'G2ForwardProcess']},
    'lmm': {'ql': ['MarketModel', 'AbcdVol', 'ExponentialForwardCorrelation', 'PiecewiseConstantCorrelation']},
    'sabr': {'ql': ['sabrVolatility', 'shiftedSabrVolatility', 'sabrFlochKennedyVolatility']},
    'black': {'ql': ['blackFormula', 'bachelierBlackFormula', 'blackFormulaImpliedStdDev', 'bachelierBlackFormulaImpliedVol']},
    'garch': {'ql': ['GJRGARCHModel', 'GJRGARCHProcess'], 'name': 'GARCH and GJR-GARCH'},
    'curve': {'ql': [c for c in inv['YieldTermStructure'] if c.startswith(('Piecewise', 'GlobalPiecewise'))
                     and 'Spread' not in c and 'Spreaded' not in c], 'variants_from_ql': True},
    'cds': {'ql': ['PiecewiseFlatHazardRate']},
    'volsurf': {'ql': ['BlackVarianceSurface', 'PiecewiseBlackVarianceSurface', 'BlackVarianceCurve']},
    'mcengine': {'ql': ['MonteCarloModel', 'PathGenerator']},
    'qmc': {'ql': ['LowDiscrepancy', 'SobolRsg']},
}
for id, f in FOLD_CORE.items():
    n = nodes[id]
    n['ql'] = f['ql']
    if 'variants' in f: n['variants'] = f['variants']
    if f.get('variants_from_ql'): n['variants'] = f['ql']
    if 'name' in f: n['name'] = f['name']

# ---------- 2. QuantLib concepts outside the curated layer
def concept(id, name, cloud, group, ql, note=None, variants=None, **kw):
    add(id, name, cloud, group, ql=ql, note=note, variants=variants, coverage=kw.pop('coverage', 'todo'), **kw)

# conventions and indexes
concept('ibor_rfr', 'IBOR / RFR indexes', 'conv', 'Indexes',
        sorted(set(inv['IborIndex']) | set(inv['OvernightIndex'])),
        'Term IBORs and overnight risk-free rates in every currency, including legacy LIBORs and the post-transition RFRs (SOFR, €STR, SONIA, SARON, TONA…).',
        variants=['Overnight RFRs: ' + ', '.join(inv['OvernightIndex']),
                  'Term rates: ' + ', '.join(sorted({re.sub(r'\d+[MWY]$|ON$|365$|SW$', '', c) for c in inv['IborIndex']} - set(inv['OvernightIndex']) - {'OvernightIndex', 'CustomIborIndex', 'DailyTenorLibor', 'Libor'}))])
concept('swapidx', 'Swap indexes (CMS)', 'conv', 'Indexes', ['SwapIndex', 'SwapSpreadIndex'], 'Constant-maturity swap rates and CMS spreads.')
concept('inflidx', 'Inflation indexes', 'conv', 'Indexes', ['ZeroInflationIndex', 'YoYInflationIndex'], 'CPI and year-on-year inflation indexes (HICP, UK RPI, US CPI…).')
concept('bmaidx', 'BMA / SIFMA index', 'conv', 'Indexes', ['BMAIndex'], 'US municipal swap index.')

# curves
YTS = inv['YieldTermStructure']
spread = [c for c in YTS if 'Spread' in c]
interp = [c for c in YTS if c not in nodes['curve']['ql'] and c not in spread and re.search(r'Curve$', c) and c not in ('FittedBondDiscountCurve',)]
concept('flat', 'Flat curve', 'curves', 'Simple curves', ['FlatForward'], 'Single continuously compounded rate: the test and teaching curve.')
concept('interp', 'Interpolated curves', 'curves', 'Simple curves', interp, 'Discount, zero or forward curves on given nodes, with a choice of interpolation.', variants=interp)
concept('multicurve', 'Multi-curve bootstrap', 'curves', 'Bootstrapped curves', ['MultiCurve'], 'Joint bootstrap of OIS discounting and IBOR forwarding curves.')
concept('fitted', 'Fitted bond curves', 'curves', 'Bootstrapped curves', ['FittedBondDiscountCurve', 'NelsonSiegelFitting', 'SvenssonFitting', 'ExponentialSplinesFitting', 'CubicBSplinesFitting', 'SimplePolynomialFitting', 'SpreadFittingMethod'],
        'Parametric curves fitted to bond prices.', variants=['Nelson-Siegel', 'Svensson', 'Exponential splines', 'Cubic B-splines', 'Simple polynomial', 'Spread fitting'])
concept('spreaded', 'Spreaded curves', 'curves', 'Curve transformations', spread + ['ZeroSpreadedTermStructure', 'ForwardSpreadedTermStructure'], 'A base curve plus a spread: basis, credit or scenario shocks.', variants=sorted(set(spread)))
concept('implied', 'Implied and composite curves', 'curves', 'Curve transformations', ['ImpliedTermStructure', 'CompositeZeroYieldStructure'], 'Forward-starting curves and curves combined from two others.')
concept('quantots', 'Quanto curve', 'curves', 'Curve transformations', ['QuantoTermStructure'], 'Drift adjustment for quanto payoffs.')
concept('ufr', 'Ultimate forward rate', 'curves', 'Curve transformations', ['UltimateForwardTermStructure'], 'Extrapolation towards a long-term rate, as in Solvency II.')
concept('flathaz', 'Flat hazard rate', 'curves', 'Credit curves', ['FlatHazardRate'], 'Constant default intensity.')
concept('interphaz', 'Interpolated credit curves', 'curves', 'Credit curves', ['HazardRateCurve', 'DefaultDensityCurve', 'SurvivalProbabilityCurve'], 'Hazard-rate, default-density or survival-probability nodes.')

# volatility
concept('constvol', 'Constant volatility', 'vol', 'Simple', ['BlackConstantVol', 'LocalConstantVol', 'ConstantSwaptionVolatility', 'ConstantOptionletVolatility', 'FlatSmileSection'], 'One number for every strike and expiry.')
concept('fxdelta', 'FX delta surface', 'vol', 'Equity and FX', ['BlackVolatilitySurfaceDelta'], 'FX volatility quoted by delta, as the market does.')
concept('hestonvol', 'Heston-implied surface', 'vol', 'Equity and FX', ['HestonBlackVolSurface'], 'The Black surface a calibrated Heston model implies.')
concept('ahvol', 'Andreasen-Huge interpolation', 'vol', 'Equity and FX', ['AndreasenHugeVolatilityAdapter', 'AndreasenHugeLocalVolAdapter', 'AndreasenHugeVolatilityInterpl'], 'Arbitrage-free interpolation of option quotes, giving both implied and local volatility.')
concept('dupire', 'Dupire local volatility surface', 'vol', 'Equity and FX', ['LocalVolSurface', 'NoExceptLocalVolSurface', 'FixedLocalVolSurface'], 'Local volatility derived from the implied surface.')
concept('swmatrix', 'Swaption volatility matrix', 'vol', 'Rates', ['SwaptionVolatilityMatrix', 'SwaptionVolatilityDiscrete', 'SpreadedSwaptionVolatility'], 'At-the-money volatility by expiry and swap tenor.')
concept('swcube', 'Swaption volatility cube', 'vol', 'Rates', ['SwaptionVolatilityCube', 'InterpolatedSwaptionVolatilityCube'], 'Adds the strike dimension to the matrix.')
concept('sabrcube', 'SABR and ZABR cubes', 'vol', 'Rates', ['SabrSwaptionVolatilityCube', 'ZabrSwaptionVolatilityCube'], 'Swaption cube with a SABR or ZABR smile per expiry and tenor.')
concept('caplet', 'Caplet volatility stripping', 'vol', 'Rates', ['OptionletStripper1', 'StrippedOptionlet', 'StrippedOptionletAdapter'], 'Caplet volatilities stripped from cap quotes.')
concept('yoyvol', 'Inflation caplet volatility', 'vol', 'Inflation', ['YoYOptionletVolatilitySurface', 'ConstantYoYOptionletVolatility', 'InterpolatedYoYOptionletVolatilityCurve', 'KInterpolatedYoYOptionletVolatilitySurface', 'YoYOptionletStripper', 'InterpolatedYoYOptionletStripper'], 'Year-on-year inflation cap and floor volatility.')
SS = inv['SmileSection']
concept('smileint', 'Interpolated smiles', 'vol', 'Smile sections', [c for c in SS if re.match(r'(Linear|Cubic|SplineCubic|MonotonicCubic)Interpolated', c)], 'Smile through market quotes with a chosen interpolation.')
concept('smilesabr', 'SABR smiles', 'vol', 'Smile sections', [c for c in SS if 'Sabr' in c], 'SABR smiles, including the no-arbitrage variant.')
concept('svi', 'SVI smiles', 'vol', 'Smile sections', [c for c in SS if 'Svi' in c], 'Stochastic volatility inspired parameterisation.')
concept('zabr', 'ZABR smiles', 'vol', 'Smile sections', [c for c in SS if 'Zabr' in c], 'SABR extension with control of the wings (short-maturity, local-vol and full finite-difference variants).')
concept('kahale', 'Kahale extrapolation', 'vol', 'Smile sections', ['KahaleSmileSection'], 'Arbitrage-free extrapolation of a smile into the wings.')

# models not in the curated layer
concept('ptdheston', 'Time-dependent Heston', 'models', 'Equity and FX', ['PiecewiseTimeDependentHestonModel'], 'Heston with piecewise-constant parameters for term structure.', lane='eq')
concept('roughheston', 'Rough Heston', 'models', 'Equity and FX', ['RoughHestonModel'], 'Fractional variance: steep short-dated skew with few parameters.', lane='eq')
concept('vg', 'Variance Gamma', 'models', 'Equity and FX', ['VarianceGammaProcess'], 'Pure-jump Lévy model.', lane='eq')
concept('cev', 'CEV', 'models', 'Equity and FX', ['AnalyticCEVEngine'], 'Constant elasticity of variance: skew from a power of spot.', lane='eq')
concept('hybrid', 'Equity-rates hybrids', 'models', 'Hybrids', ['HestonHullWhite', 'H1HW'], 'Stochastic volatility or Black-Scholes with Hull-White rates.', lane='eq')
concept('bk', 'Black-Karasinski', 'models', 'Rates', ['BlackKarasinski'], 'Lognormal short rate on a tree.', lane='rates')
concept('gsr', 'Gaussian 1-factor (GSR, Markov functional)', 'models', 'Rates', ['Gsr', 'GsrProcess', 'MarkovFunctional', 'Gaussian1dModel'], 'Workhorse for Bermudan swaptions and exotics with time-dependent volatility.', lane='rates')
concept('ou', 'Ornstein-Uhlenbeck', 'models', 'Commodities and energy', ['OrnsteinUhlenbeckProcess', 'ExtendedOrnsteinUhlenbeckProcess'], 'Mean reversion for commodity spot prices.', lane='port')
concept('kluge', 'Kluge (OU with jumps)', 'models', 'Commodities and energy', ['ExtOUWithJumpsProcess', 'KlugeExtOUProcess'], 'Mean reversion with spikes, for power prices.', lane='port')

# numerical methods
concept('trees', 'Trees and lattices', 'methods', 'Lattices and PDEs', ['BinomialTree', 'TrinomialTree'], 'Binomial trees (CRR, Jarrow-Rudd, Leisen-Reimer, Tian, Trigeorgis, Joshi, equal probabilities) and short-rate trees.')
concept('fd', 'Finite differences', 'methods', 'Lattices and PDEs', ['FdmSchemeDesc'], 'PDE solvers in one to n dimensions (Douglas, Craig-Sneyd, Hundsdorfer, modified Craig-Sneyd schemes).')
concept('lsm', 'Longstaff-Schwartz', 'methods', 'Monte Carlo', ['MCLDAmericanEngine', 'MCPRAmericanEngine'], 'Regression Monte Carlo for early exercise: the classical benchmark for callable products.')
concept('fourier', 'Fourier and COS methods', 'methods', 'Transforms and integration', ['FourierIntegration', 'COSHestonEngine', 'FFTVarianceGammaEngine'], 'Prices from the characteristic function.')
concept('approx', 'American approximations', 'methods', 'Transforms and integration', ['BaroneAdesiWhaleyApproximationEngine', 'BjerksundStenslandApproximationEngine', 'JuQuadraticApproximationEngine', 'QdPlusAmericanEngine', 'QdFpAmericanEngine'], 'Closed-form or fixed-point approximations of the early-exercise premium.')
concept('calib', 'Calibration and optimisers', 'methods', 'Calibration', ['LevenbergMarquardt', 'Simplex', 'BFGS', 'LBFGSB', 'ConjugateGradient', 'SteepestDescent', 'DifferentialEvolution', 'Cmaes', 'GaussianSimulatedAnnealing'], 'Fitting model parameters to market quotes.')
concept('cva', 'CVA and XVA', 'risk', 'Counterparty risk', [], 'Credit, funding and capital valuation adjustments on exposure profiles.', lane='xva')

# ---------- 3. instruments (folded by family)
INSTR = [
    ('vanilla', 'Vanilla options', 'Equity and FX options', ['VanillaOption', 'EuropeanOption']),
    ('quanto', 'Quanto options', 'Equity and FX options', ['QuantoVanillaOption', 'QuantoForwardVanillaOption']),
    ('fwdstart', 'Forward-start options', 'Equity and FX options', ['ForwardVanillaOption']),
    ('barrier', 'Barrier options', 'Equity and FX options', ['BarrierOption', 'QuantoBarrierOption', 'PartialTimeBarrierOption', 'SoftBarrierOption']),
    ('dbarrier', 'Double barrier options', 'Equity and FX options', ['DoubleBarrierOption', 'QuantoDoubleBarrierOption']),
    ('asian_d', 'Asian options (discrete)', 'Equity and FX options', ['DiscreteAveragingAsianOption']),
    ('asian_c', 'Asian options (continuous)', 'Equity and FX options', ['ContinuousAveragingAsianOption']),
    ('lookback', 'Lookback options', 'Equity and FX options', ['ContinuousFixedLookbackOption', 'ContinuousFloatingLookbackOption', 'ContinuousPartialFixedLookbackOption', 'ContinuousPartialFloatingLookbackOption']),
    ('cliquet', 'Cliquet options', 'Equity and FX options', ['CliquetOption']),
    ('chooser', 'Chooser options', 'Equity and FX options', ['SimpleChooserOption', 'ComplexChooserOption']),
    ('compound', 'Compound options', 'Equity and FX options', ['CompoundOption']),
    ('extensible', 'Extensible options', 'Equity and FX options', ['HolderExtensibleOption', 'WriterExtensibleOption']),
    ('basket', 'Basket and spread options', 'Multi-asset', ['BasketOption']),
    ('mountain', 'Mountain range (Everest, Himalaya)', 'Multi-asset', ['EverestOption', 'HimalayaOption']),
    ('margrabe', 'Exchange options (Margrabe)', 'Multi-asset', ['MargrabeOption']),
    ('twoasset', 'Two-asset barrier and correlation options', 'Multi-asset', ['TwoAssetBarrierOption', 'TwoAssetCorrelationOption']),
    ('varswap', 'Variance swaps', 'Equity and FX options', ['VarianceSwap']),
    ('trs', 'Equity total return swaps', 'Equity and FX options', ['EquityTotalReturnSwap']),
    ('fxfwd', 'FX forwards', 'FX', ['FxForward']),
    ('ccs', 'Cross-currency swaps', 'FX', ['ConstNotionalCrossCurrencySwap', 'ConstNotionalCrossCurrencyBasisSwap', 'ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'MtMCrossCurrencyBasisSwap']),
    ('swap', 'Interest rate swaps', 'Rates', ['Swap', 'VanillaSwap', 'FixedVsFloatingSwap', 'ZeroCouponSwap', 'MultipleResetsSwap', 'BMASwap']),
    ('ois', 'Overnight indexed swaps', 'Rates', ['OvernightIndexedSwap']),
    ('nsswap', 'Non-standard and float-float swaps', 'Rates', ['NonstandardSwap', 'FloatFloatSwap']),
    ('fra', 'FRAs and futures', 'Rates', ['ForwardRateAgreement', 'OvernightIndexFuture', 'PerpetualFutures']),
    ('capfloor', 'Caps, floors and collars', 'Rates', ['CapFloor', 'Cap', 'Floor', 'Collar']),
    ('swaption', 'Swaptions', 'Rates', ['Swaption']),
    ('bermexotic', 'Bermudan exotic swaptions', 'Rates', ['NonstandardSwaption', 'FloatFloatSwaption']),
    ('bond', 'Bonds', 'Bonds', ['Bond', 'FixedRateBond', 'FloatingRateBond', 'ZeroCouponBond', 'AmortizingFixedRateBond', 'AmortizingFloatingRateBond', 'AmortizingCmsRateBond', 'CmsRateBond']),
    ('bondfwd', 'Bond forwards', 'Bonds', ['BondForward', 'Forward']),
    ('assetswap', 'Asset swaps', 'Bonds', ['AssetSwap']),
    ('callable', 'Callable bonds', 'Bonds', ['CallableBond', 'CallableFixedRateBond', 'CallableZeroCouponBond']),
    ('convertible', 'Convertible bonds', 'Bonds', ['ConvertibleBond', 'ConvertibleFixedCouponBond', 'ConvertibleFloatingRateBond', 'ConvertibleZeroCouponBond']),
    ('cdsinstr', 'Credit default swaps', 'Credit', ['CreditDefaultSwap']),
    ('cdsopt', 'CDS options', 'Credit', ['CdsOption']),
    ('inflswap', 'Inflation swaps', 'Inflation', ['ZeroCouponInflationSwap', 'YearOnYearInflationSwap', 'CPISwap']),
    ('cpibond', 'Inflation-linked bonds', 'Inflation', ['CPIBond']),
    ('yoycap', 'Inflation caps and floors', 'Inflation', ['YoYInflationCapFloor', 'YoYInflationCap', 'YoYInflationFloor', 'YoYInflationCollar']),
    ('swing', 'Swing options', 'Commodities and energy', ['VanillaSwingOption']),
]
SKIP_INSTR = {'Option', 'OneAssetOption', 'MultiAssetOption', 'CompositeInstrument', 'Stock', 'Instrument'}
instr_of = {}
for id, name, group, ql in INSTR:
    concept('i_' + id, name, 'instruments', group, ql, variants=ql if len(ql) > 1 else None)
    for c in ql: instr_of[c] = 'i_' + id
missing = set(inv['Instrument']) - set(instr_of) - SKIP_INSTR
assert not missing, missing

# ---------- 4. engines, folded by name, grouped by the instrument they price
def fold_engine(n):
    n = re.sub(r'^MC(LD|PR)', 'MC', n)
    n = re.sub(r'^Binomial(CRR|EQP|J4|JR|LR|Tian|Trigeorgis)', 'Binomial', n)
    n = re.sub(r'^YoYInflation(Bachelier|Black|UnitDisplacedBlack)CapFloorEngine', 'YoYInflationCapFloorEngine', n)
    n = re.sub(r'^VannaVolga(IK|WO)DoubleBarrierEngine', 'VannaVolgaDoubleBarrierEngine', n)
    return n
VARIANT_NOTE = {'MC': 'pseudo-random and low-discrepancy (Sobol) variants',
                'Binomial': 'trees: CRR, EQP, Joshi, Jarrow-Rudd, Leisen-Reimer, Tian, Trigeorgis'}

MODEL_OF_TYPE = {
    'GeneralizedBlackScholesProcess': ['bs'], 'StochasticProcessArray': ['bs'],
    'HestonProcess': ['heston'], 'HestonModel': ['heston'], 'BatesModel': ['bates'], 'BatesProcess': ['bates'],
    'GJRGARCHProcess': ['garch'], 'GJRGARCHModel': ['garch'], 'PiecewiseTimeDependentHestonModel': ['ptdheston'],
    'RoughHestonModel': ['roughheston'], 'VarianceGammaProcess': ['vg'], 'ExtendedOrnsteinUhlenbeckProcess': ['ou'],
    'OrnsteinUhlenbeckProcess': ['ou'], 'ExtOUWithJumpsProcess': ['kluge'], 'HullWhite': ['hw'], 'HullWhiteProcess': ['hw'],
    'G2': ['g2'], 'Gaussian1dModel': ['gsr'], 'ShortRateModel': ['shortrate', 'hw', 'bk', 'g2'],
    'OneFactorAffineModel': ['shortrate', 'hw'], 'AffineModel': ['shortrate', 'hw'],
    'SwaptionVolatilityStructure': ['swmatrix'], 'OptionletVolatilityStructure': ['caplet'],
    'DefaultProbabilityTermStructure': ['cds'], 'YoYOptionletVolatilitySurface': ['yoyvol'],
    'LocalVolTermStructure': ['dupire'], 'SmileSection': ['smileint'],
    'IborIndex': ['ibor_rfr'], 'OvernightIndex': ['ibor_rfr'], 'InterestRateIndex': ['ibor_rfr'], 'BMAIndex': ['bmaidx'],
    'SwapIndex': ['swapidx'], 'ZeroInflationIndex': ['inflidx'], 'YoYInflationIndex': ['inflidx'],
    'DeltaVolQuote': ['fxdelta'], 'BlackVolTermStructure': ['volsurf'],
}
def method_of(name):
    m = []
    if name.startswith('MC'):
        m += ['mcengine']
        if 'American' in name: m += ['lsm']
    if name.startswith(('Binomial', 'Tree')): m += ['trees']
    if name.startswith('Fd') or name.startswith('Fd2d') or name.startswith('Fdnd'): m += ['fd']
    if name.startswith(('COS', 'FFT')) or name in ('AnalyticHestonEngine', 'AnalyticPTDHestonEngine', 'BatesEngine', 'AnalyticRoughHestonEngine', 'ExponentialFittingHestonEngine'): m += ['fourier']
    if name in ('BaroneAdesiWhaleyApproximationEngine', 'BjerksundStenslandApproximationEngine', 'JuQuadraticApproximationEngine', 'QdPlusAmericanEngine', 'QdFpAmericanEngine'): m += ['approx']
    return m
EXTRA_MODEL = {  # engines whose model is not visible in the constructor types
    'AnalyticCEVEngine': ['cev'], 'FdCEVVanillaEngine': ['cev'], 'FdSabrVanillaEngine': ['sabr'],
    'BlackSwaptionEngine': ['black'], 'BachelierSwaptionEngine': ['black'], 'BlackCapFloorEngine': ['black'],
    'BachelierCapFloorEngine': ['black'], 'BlackCdsOptionEngine': ['black'], 'BlackCallableFixedRateBondEngine': ['black'],
    'YoYInflationCapFloorEngine': ['black'], 'AnalyticHestonHullWhiteEngine': ['hybrid'], 'AnalyticH1HWEngine': ['hybrid'],
    'FdHestonHullWhiteVanillaEngine': ['hybrid'], 'AnalyticBSMHullWhiteEngine': ['hybrid'],
    'GaussianCopulaSpreadEngine': ['copula'], 'IntegralCdsEngine': ['cds'], 'MidPointCdsEngine': ['cds'], 'IsdaCdsEngine': ['cds'],
    'VannaVolgaBarrierEngine': ['fxdelta'], 'VannaVolgaDoubleBarrierEngine': ['fxdelta'],
    'FdBatesVanillaEngine': ['bates'], 'FdOrnsteinUhlenbeckVanillaEngine': ['ou'], 'FdSimpleExtOUJumpSwingEngine': ['kluge'],
    'FdHullWhiteSwaptionEngine': ['hw'], 'FdG2SwaptionEngine': ['g2'], 'G2SwaptionEngine': ['g2'],
}
DONE_ENGINES = {'AnalyticEuropeanEngine': 'black_scholes', 'MCEuropeanEngine': 'black_scholes', 'AnalyticBarrierEngine': 'black_scholes',
                'AnalyticDiscreteGeometricAveragePriceAsianEngine': 'black_scholes', 'AnalyticHestonEngine': 'heston',
                'AnalyticCapFloorEngine': 'hull_white'}

groups = defaultdict(list)
for py, rec in links.items():
    if rec['group'] == 'PricingEngine':
        groups[fold_engine(py)].append(py)
edges = set()
def edge(a, b, t='builds'):
    if a in nodes and b in nodes and a != b: edges.add((a, b, t))

instr_group = {i_id: g for _, _, g, _ in INSTR for i_id in []}
for fname, members in sorted(groups.items()):
    rec = links[members[0]]
    target = instr_of.get(rec['prices'])
    if rec['prices'] == 'ConvertibleBond': target = 'i_convertible'
    if fname.startswith('QuantoEuropean') or fname.startswith('QuantoForwardEuropean'): target = 'i_quanto'
    group = nodes[target]['name'] if target else 'Other'
    variants = None
    if len(members) > 1:
        key = 'MC' if fname.startswith('MC') else 'Binomial' if fname.startswith('Binomial') else None
        variants = [VARIANT_NOTE[key]] if key else members
    id = 'e_' + fname
    add(id, fname, 'engines', group, ql=members, variants=variants, coverage='done' if fname in DONE_ENGINES else 'todo',
        library=DONE_ENGINES.get(fname), engine=True, prices=target,
        note=f"QuantLib engine pricing {nodes[target]['name'].lower() if target else rec['prices']}.")
    if target: edge(id, target, 'prices')
    uses = set()
    for py in members:
        for t in links[py]['uses']:
            uses.update(MODEL_OF_TYPE.get(t, []))
    uses.update(EXTRA_MODEL.get(fname, []))
    for m in uses: edge(m, id)
    for m in method_of(fname): edge(m, id)
    if fname.startswith(('Discounting', 'RiskyBond')): edge('curve', id)
    if fname.startswith('Quanto'): edge('quantots', id)

# ---------- 5. other QuantLib-derived links (non-engine classes)
CLASS_NODE = {}
for n in nodes.values():
    for c in n.get('ql', []):
        if not n.get('engine') and n['cloud'] != 'instruments': CLASS_NODE.setdefault(c, n['id'])
for py, rec in links.items():
    if rec['group'] == 'PricingEngine': continue
    src = instr_of.get(py) if rec['group'] == 'Instrument' else CLASS_NODE.get(py)
    if not src: continue
    for t in rec['uses']:
        for m in MODEL_OF_TYPE.get(t, []):
            if rec['group'] == 'Instrument': edge(m, src)   # instruments build on their indexes
            elif m != src and nodes[m]['cloud'] in ('vol', 'curves', 'conv'): edge(m, src)

# ---------- 6. curated edges and hand links between concepts
for e in core['edges']:
    edge(e[0], e[1], 'quantum' if len(e) > 2 else 'builds')
HAND = [
    ('conv', 'ibor_rfr'), ('conv', 'swapidx'), ('conv', 'inflidx'), ('ibor_rfr', 'curve'), ('ibor_rfr', 'multicurve'),
    ('curve', 'multicurve'), ('flat', 'interp'), ('interp', 'curve'), ('curve', 'spreaded'), ('curve', 'implied'),
    ('curve', 'fitted'), ('curve', 'ufr'), ('curve', 'quantots'), ('flathaz', 'interphaz'), ('interphaz', 'cds'),
    ('constvol', 'volsurf'), ('volsurf', 'dupire'), ('volsurf', 'ahvol'), ('dupire', 'lv'), ('ahvol', 'lv'),
    ('heston', 'hestonvol'), ('volsurf', 'fxdelta'), ('swmatrix', 'swcube'), ('swcube', 'sabrcube'), ('sabr', 'sabrcube'),
    ('sabr', 'smilesabr'), ('smileint', 'smilesabr'), ('smileint', 'svi'), ('smilesabr', 'zabr'), ('smileint', 'kahale'),
    ('black', 'caplet'), ('black', 'swmatrix'), ('heston', 'ptdheston'), ('heston', 'roughheston'), ('bs', 'cev'),
    ('bs', 'vg'), ('heston', 'hybrid'), ('hw', 'hybrid'), ('shortrate', 'bk'), ('hw', 'gsr'), ('ou', 'kluge'),
    ('mcengine', 'lsm'), ('vr', 'lsm'), ('bs', 'trees'), ('bs', 'fd'), ('bs', 'approx'), ('heston', 'fourier'),
    ('calib', 'heston'), ('calib', 'sabr'), ('calib', 'hw'), ('calib', 'gsr'), ('pfe', 'cva'), ('cds', 'cva'),
    ('lsm', 'qae_price', 'quantum'), ('cva', 'qae_var', 'quantum'),
]
for h in HAND: edge(h[0], h[1], h[2] if len(h) > 2 else 'builds')
# instruments QuantLib prices with the engine of their base class (an OIS is a Swap, a CPI bond is a Bond…)
for e, i in [('e_DiscountingSwapEngine', 'i_ois'), ('e_DiscountingSwapEngine', 'i_nsswap'), ('e_DiscountingSwapEngine', 'i_inflswap'),
             ('e_DiscountingSwapEngine', 'i_assetswap'), ('e_DiscountingSwapEngine', 'i_trs'), ('e_DiscountingBondEngine', 'i_cpibond'),
             ('e_DiscountingBondEngine', 'i_bondfwd')]:
    edge(e, i, 'prices')

# ---------- 6b. business lines for the roadmap filter
# biz: the business lines a node belongs to (empty = shared foundation, shown in every business view)
# rlane: the roadmap row it sits in. Engines and instruments stay out of the roadmap (open them from a node).
BUSINESSES = [('rates', 'Rates'), ('eqfx', 'Equity and FX'), ('credit', 'Credit'),
              ('mrisk', 'Market risk'), ('ccr', 'Counterparty risk')]
LANE_BIZ = {'infra': [], 'mc': [], 'eq': ['eqfx'], 'rates': ['rates'], 'credit': ['credit'],
            'risk': ['mrisk'], 'port': ['mrisk'], 'xva': ['ccr']}
BIZ = {
    # quantum layer
    'qae_price': ['eqfx', 'rates'], 'qae_credit': ['credit', 'ccr'], 'qae_var': ['mrisk', 'ccr'],
    'qaoa': ['mrisk'], 'born': ['mrisk'],
    # shared foundation that only some businesses need
    'volsurf': ['eqfx', 'rates', 'mrisk'],
    # indexes
    'ibor_rfr': ['rates', 'ccr'], 'swapidx': ['rates'], 'inflidx': ['rates'], 'bmaidx': ['rates'],
    # curves
    'flat': ['rates'], 'interp': ['rates'], 'multicurve': ['rates', 'ccr'], 'fitted': ['rates'],
    'spreaded': ['rates', 'credit'], 'implied': ['rates'], 'quantots': ['eqfx'], 'ufr': ['rates'],
    'flathaz': ['credit', 'ccr'], 'interphaz': ['credit', 'ccr'],
    # volatility
    'constvol': ['eqfx'], 'fxdelta': ['eqfx'], 'hestonvol': ['eqfx'], 'ahvol': ['eqfx'], 'dupire': ['eqfx'],
    'swmatrix': ['rates'], 'swcube': ['rates'], 'sabrcube': ['rates'], 'caplet': ['rates'], 'yoyvol': ['rates'],
    'smileint': ['eqfx'], 'smilesabr': ['rates'], 'svi': ['eqfx'], 'zabr': ['rates'], 'kahale': ['eqfx'],
    # models outside the curated layer
    'ptdheston': ['eqfx'], 'roughheston': ['eqfx'], 'vg': ['eqfx'], 'cev': ['eqfx'], 'hybrid': ['eqfx', 'rates'],
    'bk': ['rates'], 'gsr': ['rates'], 'ou': ['eqfx'], 'kluge': ['eqfx'],
    # numerical methods
    'trees': ['eqfx', 'rates'], 'fd': ['eqfx', 'rates'], 'lsm': ['eqfx', 'rates'], 'fourier': ['eqfx'],
    'approx': ['eqfx'], 'calib': ['eqfx', 'rates'],
    'cva': ['ccr'],
}
CLOUD_LANE = {'conv': 'infra', 'curves': 'infra', 'vol': 'infra', 'methods': 'mc'}
BIZ_LANE = {'rates': 'rates', 'eqfx': 'eq', 'credit': 'credit', 'mrisk': 'risk', 'ccr': 'xva'}
for n in nodes.values():
    if n['cloud'] in ('engines', 'instruments'):
        continue
    if n['id'] in BIZ:
        n['biz'] = BIZ[n['id']]
    elif n.get('core'):
        n['biz'] = LANE_BIZ[n['lane']]
    else:
        raise AssertionError('no business line for ' + n['id'])
    if not n.get('core'):
        n['rlane'] = CLOUD_LANE.get(n['cloud']) or BIZ_LANE[n['biz'][0]]
for b in [b for b, _ in BUSINESSES]:
    assert any(b in n.get('biz', []) for n in nodes.values()), b

# ---------- 7. checks and output
for a, b, t in edges:
    assert a in nodes and b in nodes, (a, b)
covered = {c for n in nodes.values() for c in n.get('ql', [])}
for g in ['PricingEngine', 'CalibratedModel', 'StochasticProcess', 'YieldTermStructure', 'DefaultProbabilityTermStructure',
          'BlackVolTermStructure', 'LocalVolTermStructure', 'SwaptionVolatilityStructure', 'OptionletVolatilityStructure', 'SmileSection']:
    left = [c for c in inv[g] if c not in covered and c not in ('ShortRateModel', 'OneFactorAffineModel', 'StochasticProcess1D', 'GeneralizedBlackScholesProcess')]
    assert not left, (g, left)

out = {
    'reviewed': core['reviewed'],
    'quantlib': inv['version'],
    'lanes': core['lanes'],
    'businesses': [{'id': i, 'name': n} for i, n in BUSINESSES],
    'statuses': core['statuses'],
    'clouds': [{'id': i, 'name': n, 'note': d} for i, n, d in CLOUDS],
    'nodes': list(nodes.values()),
    'core_edges': core['edges'],
    'edges': sorted([list(e) if e[2] != 'builds' else [e[0], e[1]] for e in edges]),
}
json.dump(out, open(os.path.join(ROOT, 'public/map.json'), 'w'), indent=0, ensure_ascii=False, separators=(',', ':'))
cnt = defaultdict(int)
for n in nodes.values(): cnt[n['cloud']] += 1
print(len(nodes), 'nodes', dict(cnt), len(edges), 'edges', 'covering', len(covered), 'QuantLib classes')
