/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_MOVE_BLOCKED_NMPC_V3H
 *** Description: Additive V3H state-disturbance MPC preserving V3E envelope, delay-aware model and exporter-safe nested candidate/prediction loops
 *** Version:
***     3.9: 2026-08-26/Guilherme -  - 
 *************************************************************************/

#ifndef _MPC_MOVE_BLOCKED_NMPC_V3H_H_
#define _MPC_MOVE_BLOCKED_NMPC_V3H_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_dint.h"
#include "forte_int.h"
#include "forte_lreal.h"
#include "forte_array_at.h"


class FORTE_MPC_MOVE_BLOCKED_NMPC_V3H: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_MPC_MOVE_BLOCKED_NMPC_V3H)

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
  
  CIEC_LREAL &st_PV_MODEL() {
    return *static_cast<CIEC_LREAL*>(getDI(1));
  }
  
  CIEC_LREAL &st_APPLIED_DAC() {
    return *static_cast<CIEC_LREAL*>(getDI(2));
  }
  
  CIEC_BOOL &st_ENABLE_REQUEST() {
    return *static_cast<CIEC_BOOL*>(getDI(3));
  }
  
  CIEC_BOOL &st_EXTERNAL_HEALTHY() {
    return *static_cast<CIEC_BOOL*>(getDI(4));
  }
  
  CIEC_BOOL &st_RESET_REQUEST() {
    return *static_cast<CIEC_BOOL*>(getDI(5));
  }
  
  CIEC_LREAL &st_SP_RAW() {
    return *static_cast<CIEC_LREAL*>(getDI(6));
  }
  
  CIEC_BOOL &st_COMMAND_ENABLE() {
    return *static_cast<CIEC_BOOL*>(getDO(0));
  }
  
  CIEC_LREAL &st_COMMAND_DAC() {
    return *static_cast<CIEC_LREAL*>(getDO(1));
  }
  
  CIEC_BOOL &st_TRIPPED() {
    return *static_cast<CIEC_BOOL*>(getDO(2));
  }
  
  CIEC_INT &st_TRIP_CODE() {
    return *static_cast<CIEC_INT*>(getDO(3));
  }
  
  CIEC_LREAL &st_SELECTED_TARGET_DAC() {
    return *static_cast<CIEC_LREAL*>(getDO(4));
  }
  
  CIEC_LREAL &st_INPUT_BIAS_ESTIMATE_DAC() {
    return *static_cast<CIEC_LREAL*>(getDO(5));
  }
  
  CIEC_LREAL &st_PREDICTED_MAX_RAW() {
    return *static_cast<CIEC_LREAL*>(getDO(6));
  }
  
  CIEC_LREAL &st_PREDICTED_FINAL_RAW() {
    return *static_cast<CIEC_LREAL*>(getDO(7));
  }
  
  CIEC_BOOL &st_CONFIGURATION_VALID() {
    return *static_cast<CIEC_BOOL*>(getDO(8));
  }
  
  CIEC_BOOL &st_trip_latched_internal() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(0));
  }
  
  CIEC_INT &st_trip_code_internal() {
    return *static_cast<CIEC_INT*>(getVarInternal(1));
  }
  
  CIEC_DINT &st_history_count() {
    return *static_cast<CIEC_DINT*>(getVarInternal(2));
  }
  
  CIEC_BOOL &st_record_history_internal() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(3));
  }
  
  CIEC_BOOL &st_best_found() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(4));
  }
  
  CIEC_BOOL &st_candidate_feasible() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(5));
  }
  
  CIEC_LREAL &st_h00() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(6));
  }
  
  CIEC_LREAL &st_h01() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(7));
  }
  
  CIEC_LREAL &st_h02() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(8));
  }
  
  CIEC_LREAL &st_h03() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(9));
  }
  
  CIEC_LREAL &st_h04() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(10));
  }
  
  CIEC_LREAL &st_h05() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(11));
  }
  
  CIEC_LREAL &st_h06() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(12));
  }
  
  CIEC_LREAL &st_h07() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(13));
  }
  
  CIEC_LREAL &st_h08() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(14));
  }
  
  CIEC_LREAL &st_h09() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(15));
  }
  
  CIEC_LREAL &st_h10() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(16));
  }
  
  CIEC_LREAL &st_h11() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(17));
  }
  
  CIEC_LREAL &st_h12() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(18));
  }
  
  CIEC_LREAL &st_h13() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(19));
  }
  
  CIEC_LREAL &st_h14() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(20));
  }
  
  CIEC_LREAL &st_h15() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(21));
  }
  
  CIEC_LREAL &st_h16() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(22));
  }
  
  CIEC_LREAL &st_h17() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(23));
  }
  
  CIEC_LREAL &st_q00() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(24));
  }
  
  CIEC_LREAL &st_q01() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(25));
  }
  
  CIEC_LREAL &st_q02() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(26));
  }
  
  CIEC_LREAL &st_q03() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(27));
  }
  
  CIEC_LREAL &st_q04() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(28));
  }
  
  CIEC_LREAL &st_q05() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(29));
  }
  
  CIEC_LREAL &st_q06() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(30));
  }
  
  CIEC_LREAL &st_q07() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(31));
  }
  
  CIEC_LREAL &st_q08() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(32));
  }
  
  CIEC_LREAL &st_q09() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(33));
  }
  
  CIEC_LREAL &st_q10() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(34));
  }
  
  CIEC_LREAL &st_q11() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(35));
  }
  
  CIEC_LREAL &st_q12() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(36));
  }
  
  CIEC_LREAL &st_q13() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(37));
  }
  
  CIEC_LREAL &st_q14() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(38));
  }
  
  CIEC_LREAL &st_q15() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(39));
  }
  
  CIEC_LREAL &st_q16() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(40));
  }
  
  CIEC_LREAL &st_q17() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(41));
  }
  
  CIEC_LREAL &st_best_cost() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(42));
  }
  
  CIEC_LREAL &st_best_target() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(43));
  }
  
  CIEC_LREAL &st_best_predicted_max() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(44));
  }
  
  CIEC_LREAL &st_best_predicted_final() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(45));
  }
  
  CIEC_LREAL &st_candidate_target() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(46));
  }
  
  CIEC_LREAL &st_predicted_y() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(47));
  }
  
  CIEC_LREAL &st_predicted_u() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(48));
  }
  
  CIEC_LREAL &st_previous_u() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(49));
  }
  
  CIEC_LREAL &st_delayed_u() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(50));
  }
  
  CIEC_LREAL &st_candidate_cost() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(51));
  }
  
  CIEC_LREAL &st_candidate_predicted_max() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(52));
  }
  
  CIEC_LREAL &st_delta_u() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(53));
  }
  
  CIEC_LREAL &st_effective_input() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(54));
  }
  
  CIEC_LREAL &st_phi_value() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(55));
  }
  
  CIEC_LREAL &st_tracking_error() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(56));
  }
  
  CIEC_LREAL &st_move_value() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(57));
  }
  
  CIEC_LREAL &st_soft_excess() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(58));
  }
  
  CIEC_LREAL &st_terminal_error() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(59));
  }
  
  CIEC_LREAL &st_command_candidate() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(60));
  }
  
  CIEC_DINT &st_candidate_index() {
    return *static_cast<CIEC_DINT*>(getVarInternal(61));
  }
  
  CIEC_DINT &st_prediction_index() {
    return *static_cast<CIEC_DINT*>(getVarInternal(62));
  }
  
  CIEC_LREAL &st_disturbance_hat_internal() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(63));
  }
  
  CIEC_LREAL &st_disturbance_previous_pv_internal() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(64));
  }
  
  CIEC_BOOL &st_disturbance_previous_valid_internal() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(65));
  }
  
  CIEC_LREAL &st_disturbance_prediction_internal() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(66));
  }
  
  CIEC_LREAL &st_disturbance_innovation_internal() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(67));
  }
  

  void alg_ALG_NMPC(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateEXEC = 1;
  
  void enterStateSTART(void);
  void enterStateEXEC(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 7, 9, 68, 0);

public:
  FORTE_MPC_MOVE_BLOCKED_NMPC_V3H(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_MPC_MOVE_BLOCKED_NMPC_V3H() = default;
};

#endif // _MPC_MOVE_BLOCKED_NMPC_V3H_H_


