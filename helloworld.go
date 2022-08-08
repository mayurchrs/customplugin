package helloworld

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"strconv"
	"strings"

	"github.com/influxdata/telegraf"
	"github.com/influxdata/telegraf/plugins/inputs"
)

type Vthtest struct {
	file_path       string
	python_exe_path string
}
type Data struct {
	Python_Exe_Path  string
	Python_File_Path string
}

func (s *Vthtest) SampleConfig() string {
	fmt.Print("Working Go!")
	return "hello telegraf"
}

func (s *Vthtest) Gather(acc telegraf.Accumulator) error {

	/*
		Function for Gather average vthunder data usage using python script, and convert it into integer value.
	*/
	content, cerr := ioutil.ReadFile("/usr/local/go/src/telegraf/plugins/inputs/helloworld/path.json")
	if cerr != nil {
		log.Fatal("Error when opening file: ", cerr)
	}
	var payload Data
	jsonerr := json.Unmarshal(content, &payload)
	if jsonerr != nil {
		log.Fatal("Error during Unmarshal(): ", jsonerr)
	}

	err := os.Chmod(payload.Python_File_Path, 0755)
	cmd, _ := exec.Command(payload.Python_Exe_Path, payload.Python_File_Path).Output()

	if err != nil {
		fmt.Printf("error %s", err)
	}
	output := string(cmd)
	numRating, _ := strconv.ParseFloat(strings.TrimSpace(output), 64)

	fmt.Println(numRating)

	field := make(map[string]interface{})
	field["a10"] = numRating
	tag := make(map[string]string)
	acc.AddFields("a10", field, tag)

	return nil
}

func init() {

	content, cerr := ioutil.ReadFile("/usr/local/go/src/telegraf/plugins/inputs/helloworld/path.json")
	if cerr != nil {
		log.Fatal("Error when opening file: ", cerr)
	}
	var payload Data
	jsonerr := json.Unmarshal(content, &payload)
	if jsonerr != nil {
		log.Fatal("Error during Unmarshal(): ", jsonerr)
	}

	inputs.Add("helloworld", func() telegraf.Input {
		return &Vthtest{python_exe_path: payload.Python_Exe_Path, file_path: payload.Python_File_Path}
	})
}
