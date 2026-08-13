/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_LEVEL
 *** Description: Basic FB with empty ECC
 *** Version:
***     1.0: 2026-04-25/guilh -  - 
 *************************************************************************/

#ifndef _MPC_LEVEL_H_
#define _MPC_LEVEL_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_lreal.h"
#include "forte_uint.h"
#include "forte_array_at.h"


class FORTE_MPC_LEVEL: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_MPC_LEVEL)

private:
  static const CStringDictionary::TStringId scm_anDataInputNames[];
  static const CStringDictionary::TStringId scm_anDataInputTypeIds[];
  
  static const CStringDictionary::TStringId scm_anDataOutputNames[];
  static const CStringDictionary::TStringId scm_anDataOutputTypeIds[];
  
  static const TEventID scm_nEventREQID = 0;
  
   static const TDataIOID scm_anEIWith[];
  static const TForteInt16 scm_anEIWithIndexes[];
  static const CStringDictionary::TStringId scm_anEventInputNames[];
  
  static const TEventID scm_nEventCNFID = 0;
  
   static const TDataIOID scm_anEOWith[]; 
  static const TForteInt16 scm_anEOWithIndexes[];
  static const CStringDictionary::TStringId scm_anEventOutputNames[];
  

  static const SFBInterfaceSpec scm_stFBInterfaceSpec;

static const CStringDictionary::TStringId scm_anInternalsNames[];
static const CStringDictionary::TStringId scm_anInternalsTypeIds[];
static const SInternalVarsInformation scm_stInternalVars;
virtual void setInitialValues();
  CIEC_LREAL &st_PV() {
    return *static_cast<CIEC_LREAL*>(getDI(0));
  }
  
  CIEC_LREAL &st_SP() {
    return *static_cast<CIEC_LREAL*>(getDI(1));
  }
  
  CIEC_LREAL &st_A() {
    return *static_cast<CIEC_LREAL*>(getDI(2));
  }
  
  CIEC_LREAL &st_B() {
    return *static_cast<CIEC_LREAL*>(getDI(3));
  }
  
  CIEC_LREAL &st_C() {
    return *static_cast<CIEC_LREAL*>(getDI(4));
  }
  
  CIEC_UINT &st_HORIZON() {
    return *static_cast<CIEC_UINT*>(getDI(5));
  }
  
  CIEC_LREAL &st_DAC_MIN() {
    return *static_cast<CIEC_LREAL*>(getDI(6));
  }
  
  CIEC_LREAL &st_DAC_MAX() {
    return *static_cast<CIEC_LREAL*>(getDI(7));
  }
  
  CIEC_LREAL &st_DAC_STEP() {
    return *static_cast<CIEC_LREAL*>(getDI(8));
  }
  
  CIEC_LREAL &st_LAMBDA_DU() {
    return *static_cast<CIEC_LREAL*>(getDI(9));
  }
  
  CIEC_BOOL &st_ENABLE() {
    return *static_cast<CIEC_BOOL*>(getDI(10));
  }
  
  CIEC_BOOL &st_RESET() {
    return *static_cast<CIEC_BOOL*>(getDI(11));
  }
  
  CIEC_LREAL &st_DAC_OUT() {
    return *static_cast<CIEC_LREAL*>(getDO(0));
  }
  
  CIEC_LREAL &st_MV_PERCENT() {
    return *static_cast<CIEC_LREAL*>(getDO(1));
  }
  
  CIEC_BOOL &st_ENABLE_CMD() {
    return *static_cast<CIEC_BOOL*>(getDO(2));
  }
  
  CIEC_LREAL &st_ERR() {
    return *static_cast<CIEC_LREAL*>(getDO(3));
  }
  
  CIEC_LREAL &st_PRED_FINAL() {
    return *static_cast<CIEC_LREAL*>(getDO(4));
  }
  
  CIEC_LREAL &st_COST_MIN() {
    return *static_cast<CIEC_LREAL*>(getDO(5));
  }
  
  CIEC_LREAL &st_last_dac() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(0));
  }
  
  CIEC_LREAL &st_best_dac() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(1));
  }
  
  CIEC_LREAL &st_best_cost() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(2));
  }
  
  CIEC_LREAL &st_dac_candidate() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(3));
  }
  
  CIEC_LREAL &st_y_pred() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(4));
  }
  
  CIEC_LREAL &st_pred_error() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(5));
  }
  
  CIEC_LREAL &st_delta_dac() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(6));
  }
  
  CIEC_LREAL &st_cost() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(7));
  }
  
  CIEC_UINT &st_i() {
    return *static_cast<CIEC_UINT*>(getVarInternal(8));
  }
  
  CIEC_UINT &st_h() {
    return *static_cast<CIEC_UINT*>(getVarInternal(9));
  }
  

  void alg_ALG_MPC(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateCALC = 1;
  static const TForteInt16 scm_nStateDONE = 2;
  
  void enterStateSTART(void);
  void enterStateCALC(void);
  void enterStateDONE(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 12, 6, 10, 0);

public:
  FORTE_MPC_LEVEL(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_MPC_LEVEL() = default;
};

#endif // _MPC_LEVEL_H_


