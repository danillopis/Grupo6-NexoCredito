import sys,unittest,json,csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from api import score
from experimento import auc,psi,fit,predict,design

class ContractTests(unittest.TestCase):
    valid={'dti':.25,'utilization':.35,'prior_late':0,'monthly_income':2600}
    def test_probability_finite(self):self.assertTrue(0<score(self.valid)['pd_12m']<1)
    def test_unknown_field(self):
        with self.assertRaises(ValueError):score(dict(self.valid,default_12m=1))
    def test_missing_field(self):
        p=dict(self.valid);p.pop('dti')
        with self.assertRaises(ValueError):score(p)
    def test_infinite(self):
        with self.assertRaises(ValueError):score(dict(self.valid,dti=float('inf')))
    def test_nan(self):
        with self.assertRaises(ValueError):score(dict(self.valid,dti=float('nan')))
    def test_negative_income(self):
        with self.assertRaises(ValueError):score(dict(self.valid,monthly_income=-20))
    def test_excess_dti(self):
        with self.assertRaises(ValueError):score(dict(self.valid,dti=1.1))
    def test_boolean_not_number(self):
        with self.assertRaises(ValueError):score(dict(self.valid,prior_late=True))
    def test_late_binary(self):
        with self.assertRaises(ValueError):score(dict(self.valid,prior_late=2))
    def test_manual_high_dti(self):self.assertEqual(score(dict(self.valid,dti=.8))['decision'],'REVISION_MANUAL')
    def test_hotfix_guard(self):
        p=json.loads((ROOT/'config/politica.json').read_text());p['review_interaction']=True
        r=score(dict(self.valid,dti=.32,utilization=.6),p)
        self.assertIn('INTERACCION_EN_REVISION',r['reasons'])
    def test_no_real_authorization(self):self.assertTrue(score(self.valid)['simulation'])
    def test_same_input_same_score(self):self.assertEqual(score(self.valid),score(self.valid))
    def test_amount_missing_not_imputed(self):
        with self.assertRaises(ValueError):score(dict(self.valid,monthly_income=None))

class MetricTests(unittest.TestCase):
    def test_auc_ties(self):self.assertEqual(auc(np.array([0,1]),np.array([.5,.5])),.5)
    def test_auc_perfect(self):self.assertEqual(auc(np.array([0,0,1,1]),np.array([.1,.2,.8,.9])),1)
    def test_auc_inverse(self):self.assertEqual(auc(np.array([1,1,0,0]),np.array([.1,.2,.8,.9])),0)
    def test_psi_identical(self):self.assertEqual(psi(np.array([.1,.2]),np.array([.1,.2])),0)
    def test_psi_empty_bin_finite(self):self.assertTrue(np.isfinite(psi(np.zeros(100),np.ones(100))))
    def test_nonlinear_interaction_zero(self):self.assertEqual(design(np.array([[.1,.8,0,0]]),True)[0,-1],0)

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads((ROOT/'resultados/resumen.json').read_text())
    def test_covariate_drift(self):self.assertGreater(self.r['monitoring'][2]['psi_score'],.25)
    def test_concept_invisible_to_psi(self):self.assertLess(self.r['monitoring'][3]['psi_score'],.10)
    def test_concept_bad_calibration(self):self.assertGreater(self.r['monitoring'][3]['oe'],1.25)
    def test_auc_can_improve_while_brier_worsens(self):
        x=self.r['monitoring'][3];self.assertGreater(x['auc'],self.r['base']['auc']);self.assertGreater(x['brier'],self.r['base']['brier'])
    def test_candidate_calibration(self):self.assertTrue(.8<=self.r['holdout_june']['Candidato']['oe']<=1.25)
    def test_candidate_brier(self):self.assertLess(self.r['holdout_june']['Candidato']['brier'],self.r['holdout_june']['Vigente']['brier']-.01)
    def test_18000_scoring_rows(self):self.assertEqual(self.r['total_scoring'],18000)
    def test_npl_reconciles(self):self.assertAlmostEqual(self.r['stock_npl'],self.r['stock_npl_balance']/self.r['stock_balance'])
    def test_churn_is_exposure_weighted(self):
        with (ROOT/'datos/crm.csv').open() as f:rows=list(csv.DictReader(f))
        actual=sum(int(r['churned']) for r in rows)/sum(int(r['active_start']) for r in rows)
        self.assertAlmostEqual(actual,self.r['churn'])
    def test_unique_application_ids(self):
        with (ROOT/'datos/scoring.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),len({r['application_id'] for r in rows}))

if __name__=='__main__':unittest.main(verbosity=2)
