<?php
namespace Core\Language\Controllers;
use \Statickidz\GoogleTranslate;

class Language extends \CodeIgniter\Controller
{
    public function __construct(){
        $this->config = parse_config( include realpath( __DIR__."/../Config.php" ) );
        $this->model = new \Core\Language\Models\LanguageModel();
    }

    public function index( $page = "empty", $ids = false ) {

        

        $result = db_fetch("*", TB_LANGUAGE_CATEGORY, "", "id", "ASC");
        
        $data = [
            "result" => $result,
            "title" => $this->config['name'],
            "desc" => $this->config['desc'],
        ];

        switch ($page) {
            case 'translate':

                /*Update new language item*/
                $this->update_language_item($ids);
                /*End update language item*/


                $start = 0;
                $limit = 1;

                $pager = \Config\Services::pager();
                $total = $this->model->get_list($ids,  false);
                $datatable = [
                    "responsive" => true,
                    "columns" => [
                        "text" => __("Text"),
                    ],
                    "total_items" => $total,
                    "per_page" => 50,
                    "current_page" => 1,

                ];

                $data_content = [
                    'start' => $start,
                    'limit' => $limit,
                    'total' => $total,
                    'pager' => $pager,
                    'code'  => $ids,
                    'datatable'  => $datatable,
                    'config' => $this->config
                ];

                $data['content'] = view('Core\Language\Views\translate', $data_content);
                break;

            case 'update':
                $item = db_get("*", TB_LANGUAGE_CATEGORY, "ids = '{$ids}'");
                $data_content = [
                    "item" => $item,
                    "language_codes" => get_language_codes(),
                ];

                $data['content'] = view('Core\Language\Views\update', $data_content);
                break;
            
            default:
                create_default_language();
                $data['content'] = view('Core\Language\Views\empty');
                break;
        }

        return view('Core\Language\Views\index', $data);
    }

    public function ajax_list($code){
        $total_items = $this->model->get_list($code, false);
        $result = $this->model->get_list($code, true);
        $data = [
            "result" => $result
        ];
        ms( [
            "total_items" => $total_items,
            "data" => view('Core\Language\Views\ajax_translate', $data)
        ] );
    }

    public function save($ids = ""){
        $status = post('status');
        $name = post('name');
        $code = post('code');
        $icon = post('icon');
        $dir = post('dir');
        $translate = post('translate');
        $is_default = post('is_default');

        $item = db_get("*", TB_LANGUAGE_CATEGORY, "ids = '{$ids}'");

        $language_categories = db_fetch("*", TB_LANGUAGE_CATEGORY, ["is_default" => true]);
        if(empty($language_categories)){
            $is_default = true;
        }else{
            if($is_default){
                db_update(TB_LANGUAGE_CATEGORY, array("is_default" => false));
            }
        }

        if (! $this->validate(['name' => 'required'])) {
            ms([
                "status" => "error",
                "message" => __("Name is required")
            ]);
        }

        if (! $this->validate(['status' => 'required'])) {
            ms([
                "status" => "error",
                "message" => __("Status is required")
            ]);
        }

        if (! $this->validate(['code' => 'required'])) {
            ms([
                "status" => "error",
                "message" => __("Code is required")
            ]);
        }

        if (! $this->validate(['dir' => 'required'])) {
            ms([
                "status" => "error",
                "message" => __("Text direction is required")
            ]);
        }

        if (! $this->validate(['icon' => 'required'])) {
            ms([
                "status" => "error",
                "message" => __("Icon is required")
            ]);
        }

        if(!$item){
            $check_code = db_get("*", TB_LANGUAGE_CATEGORY, ["code" => $code]);
            if (! empty($check_code) ) {
                ms([
                    "status" => "error",
                    "message" => __("This language already exists")
                ]);
            }

            db_delete(TB_LANGUAGE,  ['code' => $code]);

            db_insert(TB_LANGUAGE_CATEGORY , [ 
                "ids" => ids(),
                "name" => $name,
                "code" => $code,
                "icon" => $icon,
                "dir"  => $dir,
                "is_default" => $is_default,
                "auto_translate" => $translate,
                "status" => $status
            ]);

            if($translate != ""){

                $texts_arr = [];
                $texts = "";

                $language_default = db_fetch("*", TB_LANGUAGE, ["code" => "en"]);
                if( !empty($language_default) ){
                    foreach ($language_default as $key => $value) {
                        
                        if( strlen($texts) > 3500 ){
                            $texts = substr($texts, 0,  -1*strlen("\n[-]") );
                            $texts_arr[] = $texts;
                            $texts = $value->text."\n[-]";
                        }else{
                            $texts .= $value->text."\n[-]";
                        }

                        if(count($language_default) == $key + 1 && strlen($texts) <= 3500){
                            $texts_arr[] = $texts;
                        }
                    }
                }

                $source = "en";
                $target = $translate;

                $results = [];
                if(!empty($texts_arr)){

                    try {
                        foreach ($texts_arr as $values) {
                            $trans = new \Statickidz\GoogleTranslate();
                            $results[] = $trans->translate($source, $target, $values);
                        }   
                    } catch (\Exception $e) {
                        ms([
                            "status" => "error",
                            "message" => $e->getMessage()
                        ]);
                    }

                    $text_trans = [];
                    if( !empty($results) ){
                        foreach ($results as $key => $texts) {
                            $texts = str_replace("HH: MM", "HH:MM", $texts);
                            $texts = str_replace("© ", "©", $texts);
                            $texts = str_replace("# ", "#", $texts);
                            $texts = str_replace("[-] ", "[-]", $texts);
                            $texts = str_replace("% s", "%s", $texts);
                            $texts = str_replace("% d", "%d", $texts);
                            $texts = str_replace("％s", "%s", $texts);
                            $texts = str_replace("\n", "", $texts);
                            $texts = str_replace("\r", "", $texts);
                            $texts = explode("[-]", $texts);
                            $text_trans = array_merge($text_trans, $texts);
                        }

                    }

                    if(!empty($text_trans)){
                        foreach ($language_default as $key => $value) {
                            db_insert(TB_LANGUAGE, 
                                [
                                    "ids"  => ids(),
                                    "code" => $code,
                                    "text" => $text_trans[$key],
                                    "slug" => $value->slug,
                                    "custom" => 0,
                                ]
                            );
                        }
                    }
                }
            }
        }else{
            $check_code = db_get("*", TB_LANGUAGE_CATEGORY, "ids != '{$ids}' AND code = '{$code}'");
            if (! empty($check_code) ) {
                ms([
                    "status" => "error",
                    "message" => __("This language already exists")
                ]);
            }

            db_update(
                TB_LANGUAGE_CATEGORY, 
                [
                    "name" => $name,
                    "code" => $code,
                    "icon" => $icon,
                    "dir"  => $dir,
                    "is_default" => $is_default,
                    "status" => $status,
                ], 
                array("ids" => $ids)
            );
        }

        create_language_file($code);

        ms([
            "status"  => "success",
            "message" => __('Success'),
        ]);
    }

    public function save_item($code = ""){
        $ids = post('ids');
        $text = post('text');

        $language_categories = db_get("*", TB_LANGUAGE, ["ids" => $ids]);

        if(!$language_categories){
            ms([
                "status" => "error",
                "message" => __("Language item does not exist")
            ]);
        }
        
        db_update(
            TB_LANGUAGE,
            ["text" => $text],
            ["ids" => $ids]
        );

        create_language_file($code);

        ms([
            "status"  => "success",
            "message" => __('Success'),
        ]);
    }

    public function export($code = ""){
        $lang_file = WRITEPATH."lang/".$code.".json";

        if(!file_exists($lang_file)){
            redirect_to( get_module_url() );
        }

        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename='.basename("lang_".$code.'.json'));
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        header('Content-Length: ' . filesize($lang_file));
        readfile($lang_file);

        exit();

    }

    public function do_import(){
        $team_id = get_team("id");
        $max_size = 2*1024;
        $file_path = "";

        if(!empty($_FILES) && is_array($_FILES['files']['name'])){
            if(empty( $this->request->getFiles() )){
                ms([
                    "status" => "error",
                    "message" => __('Cannot found files json to upload')
                ]);
            }

            $check_mime = $this->validate([
                'files' => [
                    'uploaded[files]',
                    'ext_in[files,json]'
                ],
            ]);

            if(!$check_mime){
                ms([
                    "status" => "error",
                    "message" => "The filetype you are attempting to upload is not allowed"
                ]);
            }

            $check_size = $this->validate([
                'files' => [
                    'uploaded[files]',
                    'max_size[files,'.$max_size.']'
                ],
            ]);

            if(!$check_size){
                ms([
                    "status" => "error",
                    "message" => __( sprintf("Unable to upload a file larger than %sMB", $maxsize) )
                ]);
            }

            if ($file = $this->request->getFiles()) {
                if( isset( $file['files'] ) ){
                    foreach($file['files'] as $img) {
                        if ($img->isValid() && ! $img->hasMoved()) {
                            $newName = $img->getRandomName();
                            $img->move(WRITEPATH.'tmp', $newName);
                            $file_path = WRITEPATH.'tmp/'.$newName;
                        }
                    }
                }
            }
        }

        if($file_path == ""){
            ms([
                "status" => "error",
                "message" => __("Upload csv file failed.")
            ]);
        }

        $language_data = file_get_contents($file_path);
        unlink($file_path);
        $language_data = json_decode($language_data, 1);

        if(
            isset($language_data["info"]) && 
            isset($language_data["info"]["name"]) && 
            isset($language_data["info"]["icon"]) && 
            isset($language_data["info"]["code"]) && 
            isset($language_data["info"]["dir"])
        ){

            $language_category = $language_data["info"];
            db_delete(TB_LANGUAGE_CATEGORY, ["code" => $language_category["code"]]);

            $is_default = 0;
            $language_list = db_fetch("*", TB_LANGUAGE_CATEGORY, ["is_default" => 1]);
            if(empty($language_list)){
                $is_default = 1;
            }

            $data_cate = array(
                "ids"         => ids(),
                "name"        => $language_category["name"],
                "icon"        => $language_category["icon"],
                "code"        => $language_category["code"],
                "dir"         => $language_category["dir"],
                "is_default"  => $is_default,
                "status"      => 1,
            );

            db_insert(TB_LANGUAGE_CATEGORY, $data_cate);

            if(isset($language_data["data"]) && !empty($language_data["data"])){
                db_delete(TB_LANGUAGE, ["code" => $language_category["code"]]);
                foreach ($language_data["data"] as $key => $value) {
                    db_insert(TB_LANGUAGE, array(
                        "ids"  => ids(),
                        "code" => $language_category["code"], 
                        "text" => $value, 
                        "slug" => $key
                    ));
                }
            }

            /*EXPORT LANGUAGE*/
            $language_cate = db_get("*", TB_LANGUAGE_CATEGORY, ["code" => $language_category["code"]]);
            $language_items = db_fetch("slug, text", TB_LANGUAGE, ["code" => $language_category["code"]]);
            if(!empty($language_cate)){
                $language = array();
                if(!empty($language_items)){
                    foreach ($language_items as $key => $value) {
                        $language[$value->slug] = $value->text;
                    }
                }

                $category = [
                    "name"        => $language_cate->name,
                    "icon"        => $language_cate->icon,
                    "code"        => $language_cate->code
                ];

                $language_pack = [
                    "info" => $language_cate,
                    "data" => $language
                ];

                $language_pack = json_encode($language_pack);

                create_folder(WRITEPATH."lang");
                $handle = fopen(WRITEPATH."lang/".$language_cate->code.".json", "w");
                fwrite($handle, $language_pack);
                fclose($handle);
            }
            /*END EXPORT LANGUAGE*/
        }else{
            ms(array(
                "status"  => "error",
                "message" => __("Language package is invalid")
            ));
        }

        ms([
            "status" => "success",
            "message" => __('Import successfully')
        ]);
    }

    public function delete( $ids = '' ){
        if($ids == ''){
            $ids = post('id');
        }

        if( empty($ids) ){
            ms([
                "status" => "error",
                "message" => __('Please select an item to delete')
            ]);
        }

        $language = db_get("id,code", TB_LANGUAGE_CATEGORY, ["ids" => $ids]);

        if(empty($language)){
            ms([
                "status" => "success",
                "message" => __('Cannot found language you want delete')
            ]);
        }

        db_delete(TB_LANGUAGE_CATEGORY, ['id' => $language->id]);
        db_delete(TB_LANGUAGE, ['code' => $language->code]);

        ms([
            "status" => "success",
            "message" => __('Success')
        ]);
    }

    private function update_language_item($code){

        $language_category = db_get("*", TB_LANGUAGE_CATEGORY, "code = '{$code}'");
        if($language_category){
            $target = $language_category->auto_translate;

            $module_paths = get_module_paths();
            $language_data = array();
            if(!empty($module_paths))
            {
                if( !empty($module_paths) ){
                    foreach ($module_paths as $key => $module_path) {
                        $lang_paths = $module_path . "/Language/";
                        $lang_files = glob( $lang_paths . '*' );

                        if ( !empty( $lang_files ) )
                        {
                            foreach ( $lang_files as $lang_file )
                            {
                                $lang_content = include $lang_file;
                                $language_data[] = $lang_content;

                            }
                        }
                    }
                }
            }

            $language_data = array_flatten($language_data);

            $language_items = [];
            foreach ($language_data as $key => $text) {
                $check_exist = db_get("*", TB_LANGUAGE, "code = '{$code}' AND slug = '".md5($key)."'");
                if(empty( $check_exist )){

                    if($target != ""){
                        try {
                            $trans = new \Statickidz\GoogleTranslate();
                            $text = $trans->translate("en", $target, $text);

                            $text = str_replace("HH: MM", "HH:MM", $text);
                            $text = str_replace("© ", "©", $text);
                            $text = str_replace("# ", "#", $text);
                            $text = str_replace("[-] ", "[-]", $text);
                            $text = str_replace("% s", "%s", $text);
                            $text = str_replace("% d", "%d", $text);
                            $text = str_replace("％s", "%s", $text);
                            $text = str_replace("\n", "", $text);
                            $text = str_replace("\r", "", $text);
                        } catch (\Exception $e) {}
                    }

                    $language_items[] = [
                        "ids" => ids(),
                        "code" => $code,
                        "slug" => md5($key),
                        "text" => $text,
                        "custom" => 0
                    ];
                }
            }

            db_insert( TB_LANGUAGE, $language_items );

            create_language_file($code);
        }
    }
}
