// The four layers of the model map: conventional models, acceleration, quantum adaptation, quantum hardware.
// Shared by the map's 3D overview and the home animation.
export const LAYERS = ['Conventional models', 'Acceleration', 'Quantum adaptation', 'Quantum hardware'];
// bottom-layer components with a path upward (the rest of the library is drawn as faint dust)
export const UP = new Set(['heston', 'slv', 'lmm', 'lsm', 'mcengine', 'qmc', 'vr', 'mcvar', 'pfe', 'cva', 'cpm', 'card', 'gen']);
// existing components lifted to an upper layer: [layer, component it stands above]
export const LIFT = { gpu: [1, 'mcengine'], aad: [1, 'vr'], qae_price: [2, 'heston'], qae_var: [2, 'pfe'], qae_credit: [2, 'cpm'], qaoa: [2, 'card'], born: [2, 'gen'] };
export const EXTRA = [
  ['hg', 'Heston on GPU', 1, 'heston', 'models'], ['sg', 'SLV on GPU', 1, 'slv', 'models'], ['lg', 'LMM on GPU', 1, 'lmm', 'models'],
  ['lsg', 'Longstaff-Schwartz on GPU', 1, 'lsm', 'methods'], ['vg', 'Monte Carlo VaR on GPU', 1, 'mcvar', 'risk'], ['eg', 'Exposure on GPU', 1, 'pfe', 'risk'], ['cg', 'Credit portfolio MC on GPU', 1, 'cpm', 'risk'],
  ['load', 'Data loading', 2, 'mcengine', 'infra'], ['res', 'Resource estimation', 2, 'cva', 'infra', 6, 6],
  ['qpu', 'Cloud QPU access', 3, 'mcengine', 'infra'], ['sec', 'Contract and security review', 3, 'mcengine', 'infra', -14, 6], ['orch', 'Hybrid orchestration', 3, 'mcengine', 'infra', 14, 6], ['ft', 'Fault-tolerant QPU (2030+)', 3, 'mcengine', 'infra', 6, -10],
].map(([id, name, layer, above, cloud, dx = 0, dz = 0]) => ({ id, name, layer, above, cloud, dx, dz, extra: true, coverage: 'todo', biz: [] }));
export const LEDGES = [['heston', 'hg'], ['slv', 'sg'], ['lmm', 'lg'], ['lsm', 'lsg'], ['mcvar', 'vg'], ['pfe', 'eg'], ['cva', 'eg'], ['cpm', 'cg'], ['mcengine', 'gpu'], ['qmc', 'gpu'], ['vr', 'gpu'], ['mcengine', 'aad'],
  ['hg', 'qae_price'], ['lsg', 'qae_price'], ['vg', 'qae_var'], ['eg', 'qae_var'], ['cg', 'qae_credit'], ['card', 'qaoa'], ['gen', 'born'], ['gpu', 'load'],
  ['qae_price', 'qpu'], ['qae_var', 'qpu'], ['qae_credit', 'qpu'], ['qaoa', 'qpu'], ['born', 'qpu'], ['sec', 'qpu'], ['orch', 'qpu'], ['qpu', 'ft']];
export const layerOf = (n) => n.extra ? n.layer : LIFT[n.id] ? LIFT[n.id][0] : 0;
export const aboveOf = (n) => n.extra ? n.above : LIFT[n.id] ? LIFT[n.id][1] : null;
export const isDust = (n) => !n.extra && !n.quantum && !LIFT[n.id] && !UP.has(n.id);
export const LY = 13;
