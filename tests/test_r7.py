"""benchmark-r7 additions: claim text, SM-PAM docstring/thresholds, phycom CSV uniqueness, lambert_m on-axis no-op,
factorial design and default-cell CRN identity."""
import os, numpy as np, pandas as pd, pytest
from channel import physical as ph
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(ROOT, *p)
STALE = ('3.25 m was not run with oracle', 'only on the sweep seeds', '3.25 and 3.5 m were not perturbed')

def test_claim_text_r7():
    for f in ('README.md', 'METHODS.md', 'results/benchmark/SUMMARY.md', 'results/benchmark/CLAIMS_r7.md'):
        s = open(R(f)).read()
        for st in STALE: assert st not in s, (f, st)
        assert 'with the ASSUMED default optics (f = 6 mm, f/2.0, focus 1.0 m), the 65 mm 8×8 panel on axis' in s, f
        assert 'all Holm-significant (56-claim family)' in s and 'CFA crosstalk ×2' in s, f

def test_smpam_analytic_thresholds_m4():
    # use the registry-loaded plugin class (a second import would re-register a distinct class and raise)
    import ast
    from occbench import registry
    registry.load_plugins()
    s = next(o() if isinstance(o, type) else o() for o in registry._REG.values() if type(o() if isinstance(o, type) else o()).__name__ == 'SMPAMLeblebici')
    assert s.M == 4 and np.allclose(s.thresholds, [2 / 7, 4 / 7, 6 / 7])
    doc = ast.get_docstring(ast.parse(open(R('schemes_contrib/sm_pam_leblebici.py')).read()))
    assert 'tuned on TUNE_SEED' not in doc and 'ANALYTIC midpoints' in doc

def test_phycom_margins_no_duplicates():
    d = pd.read_csv(R('results/benchmark/r6/phycom_margins.csv'))
    assert not d.duplicated().any() and not d.duplicated(['distance_m', 'vs', 'crc', 'kind']).any()
    assert len(d) == 6 * 5

def test_lambert_m_is_noop_on_axis_only():
    p0, p1 = dict(ph.P), dict(ph.P, lambert_m=1.56)
    assert np.allclose(ph.received_photons(3.0, 0.0, 0.0, p0), ph.received_photons(3.0, 0.0, 0.0, p1))
    assert not np.allclose(ph.received_photons(3.0, 30.0, 30.0, p0), ph.received_photons(3.0, 30.0, 30.0, p1))

def test_factorial_design():
    from experiments.revision_r7 import fact_cells, jobs_for, FACT
    c = fact_cells(); assert len(c) == 36 and dict(focus_m='1.0', f_mm='6', f_number='2.0', brightness='1/128') in c
    assert len(jobs_for('fact')) == 36 * 2 * 2 and len(jobs_for('lamb30')) == 8
    assert (FACT['focus_m']['1.0'], FACT['f_mm']['6'], FACT['f_number']['2.0'], FACT['brightness']['1/128']) == \
        (ph.P['focus_m'], ph.P['f_mm'], ph.P['f_number'], ph.P['brightness'])

def test_factorial_default_cell_crn_identity():
    f = R('results/benchmark/r7/factorial_default_identity.csv')
    if not os.path.exists(f): pytest.skip('r7 factorial not run')
    d = pd.read_csv(f); assert len(d) > 0 and d.identical.all()
