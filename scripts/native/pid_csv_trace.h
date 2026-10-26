// Diagnostic instrumentation only: one PID instance and one initialization per process.
#pragma once
#include <fstream>
#include <iostream>
#include <iomanip>
#include <locale>
#include <cstdlib>
#include <chrono>
namespace pid_trace {
struct Writer {
  std::ofstream file;
  const void* owner;
  unsigned sample;
  bool initialized;
  std::chrono::steady_clock::time_point start;
  Writer(): owner(0), sample(0), initialized(false) {}
  void init(const void* instance) {
    if(initialized) { file.close(); std::cerr << "PID_TRACE ERROR: restart FORTE for each trial\n"; return; }
    initialized=true; owner=instance; start=std::chrono::steady_clock::now();
    const char* path=std::getenv("PID_TRACE_FILE");
    if(!path || !*path) { std::cerr << "PID_TRACE disabled: PID_TRACE_FILE missing\n"; return; }
    std::ifstream existing(path);
    if(existing.good()) { std::cerr << "PID_TRACE ERROR: output exists\n"; return; }
    file.open(path, std::ios::out); file.imbue(std::locale::classic());
    if(!file) { std::cerr << "PID_TRACE ERROR: cannot open output\n"; return; }
    file << "sample,elapsed_wall_s,setpoint,process_output,command,proportional_gain,integral_gain,derivative_gain\n";
    file.flush(); std::cerr << "PID_TRACE ready\n";
  }
  void row(const void* instance, double sp, double pv, double mv, double kp, double ki, double kd) {
    if(!file.is_open()) return;
    if(instance!=owner) { file.close(); std::cerr << "PID_TRACE ERROR: multiple instances\n"; return; }
    const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    file << std::setprecision(17) << ++sample << ',' << elapsed << ',' << sp << ',' << pv << ',' << mv << ',' << kp << ',' << ki << ',' << kd << '\n';
    file.flush();
    if(!file) { file.close(); std::cerr << "PID_TRACE ERROR: write failed\n"; }
  }
};
inline Writer& writer() { static Writer instance; return instance; }
}
