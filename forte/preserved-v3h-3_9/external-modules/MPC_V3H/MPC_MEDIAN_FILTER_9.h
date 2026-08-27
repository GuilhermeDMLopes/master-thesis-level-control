/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_MEDIAN_FILTER_9
 *** Description: Deterministic 9-sample rolling median for the raw-count MPC model coordinate
 *** Version:
***     1.0: 2026-08-10/Guilherme -  - 
 *************************************************************************/

#ifndef _MPC_MEDIAN_FILTER_9_H_
#define _MPC_MEDIAN_FILTER_9_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_lreal.h"
#include "forte_array_at.h"


class FORTE_MPC_MEDIAN_FILTER_9: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_MPC_MEDIAN_FILTER_9)

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
  CIEC_LREAL &st_PV_RAW() {
    return *static_cast<CIEC_LREAL*>(getDI(0));
  }
  
  CIEC_BOOL &st_RESET() {
    return *static_cast<CIEC_BOOL*>(getDI(1));
  }
  
  CIEC_LREAL &st_PV_MEDIAN() {
    return *static_cast<CIEC_LREAL*>(getDO(0));
  }
  
  CIEC_BOOL &st_INITIALIZED() {
    return *static_cast<CIEC_BOOL*>(getDO(1));
  }
  
  CIEC_BOOL &st_initialized_internal() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(0));
  }
  
  CIEC_LREAL &st_v0() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(1));
  }
  
  CIEC_LREAL &st_v1() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(2));
  }
  
  CIEC_LREAL &st_v2() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(3));
  }
  
  CIEC_LREAL &st_v3() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(4));
  }
  
  CIEC_LREAL &st_v4() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(5));
  }
  
  CIEC_LREAL &st_v5() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(6));
  }
  
  CIEC_LREAL &st_v6() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(7));
  }
  
  CIEC_LREAL &st_v7() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(8));
  }
  
  CIEC_LREAL &st_v8() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(9));
  }
  
  CIEC_LREAL &st_s0() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(10));
  }
  
  CIEC_LREAL &st_s1() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(11));
  }
  
  CIEC_LREAL &st_s2() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(12));
  }
  
  CIEC_LREAL &st_s3() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(13));
  }
  
  CIEC_LREAL &st_s4() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(14));
  }
  
  CIEC_LREAL &st_s5() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(15));
  }
  
  CIEC_LREAL &st_s6() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(16));
  }
  
  CIEC_LREAL &st_s7() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(17));
  }
  
  CIEC_LREAL &st_s8() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(18));
  }
  
  CIEC_LREAL &st_swap_value() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(19));
  }
  

  void alg_ALG_MEDIAN(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateEXEC = 1;
  
  void enterStateSTART(void);
  void enterStateEXEC(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 2, 2, 20, 0);

public:
  FORTE_MPC_MEDIAN_FILTER_9(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_MPC_MEDIAN_FILTER_9() = default;
};

#endif // _MPC_MEDIAN_FILTER_9_H_


